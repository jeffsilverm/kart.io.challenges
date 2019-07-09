#! /usr/bin/python3
# -*- coding: utf-8 -*-
#
#
# This program tests an arbitrary number of nameservers.
# There is a configuration file which has a list of nameservers.  Each
# nameserver has a list of things to look up.
# For each thing to look up, there is the name of the thing
# the type of the thing (an RR as defined by IANA
# https://www.iana.org/assignments/dns-parameters/dns-parameters.xhtml
#

import json
import sys
import traceback

import DNS

import socket, string, types, time, select
import Type,Class,Opcode
import asyncore
#
# This random generator is used for transaction ids and port selection.  This
# is important to prevent spurious results from lost packets, and malicious
# cache poisoning.  This doesn't matter if you are behind a caching nameserver
# or your app is a primary DNS server only. To install your own generator,
# replace DNS.Base.random.  SystemRandom uses /dev/urandom or similar source.
#
try:
  from random import SystemRandom
  random = SystemRandom()
except:
  import random

class DNSError(Exception): pass
class ArgumentError(DNSError): pass
class SocketError(DNSError): pass
class TimeoutError(DNSError): pass

class ServerError(DNSError):
    def __init__(self, message, rcode):
        DNSError.__init__(self, message, rcode)
        self.message = message
        self.rcode = rcode

class IncompleteReplyError(DNSError): pass

# Lib uses some of the above exception classes, so import after defining.
import Lib

defaults= { 'protocol':'udp', 'port':53, 'opcode':Opcode.QUERY,
            'qtype':Type.A, 'rd':1, 'timing':1, 'timeout': 30,
            'server_rotate': 0 }

defaults['server']=[]

def ParseResolvConf(resolv_path="/etc/resolv.conf"):
    "parses the /etc/resolv.conf file and sets defaults for name servers"
    global defaults
    lines=open(resolv_path).readlines()
    for line in lines:
        line = string.strip(line)
        if not line or line[0]==';' or line[0]=='#':
            continue
        fields=string.split(line)
        if len(fields) < 2:
            continue
        if fields[0]=='domain' and len(fields) > 1:
            defaults['domain']=fields[1]
        if fields[0]=='search':
            pass
        if fields[0]=='options':
            pass
        if fields[0]=='sortlist':
            pass
        if fields[0]=='nameserver':
            defaults['server'].append(fields[1])

def DiscoverNameServers():
    import sys
    if sys.platform in ('win32', 'nt'):
        import win32dns
        defaults['server']=win32dns.RegistryResolve()
    else:
        return ParseResolvConf()

class DnsRequest:
    """ high level Request object """
    def __init__(self,*name,**args):
        self.donefunc=None
        self.async=None
        self.defaults = {}
        self.argparse(name,args)
        self.defaults = self.args
        self.tid = 0

    def argparse(self,name,args):
        if not name and self.defaults.has_key('name'):
            args['name'] = self.defaults['name']
        if type(name) is types.StringType:
            args['name']=name
        else:
            if len(name) == 1:
                if name[0]:
                    args['name']=name[0]
        if defaults['server_rotate'] and \
                type(defaults['server']) == types.ListType:
            defaults['server'] = defaults['server'][1:]+defaults['server'][:1]
        for i in defaults.keys():
            if not args.has_key(i):
                if self.defaults.has_key(i):
                    args[i]=self.defaults[i]
                else:
                    args[i]=defaults[i]
        if type(args['server']) == types.StringType:
            args['server'] = [args['server']]
        self.args=args

    def socketInit(self,a,b):
        self.s = socket.socket(a,b)

    def processUDPReply(self):
        if self.timeout > 0:
            r,w,e = select.select([self.s],[],[],self.timeout)
            if not len(r):
                raise TimeoutError, 'Timeout'
        (self.reply, self.from_address) = self.s.recvfrom(65535)
        self.time_finish=time.time()
        self.args['server']=self.ns
        return self.processReply()

    def _readall(self,f,count):
      res = f.read(count)
      while len(res) < count:
        if self.timeout > 0:
            # should we restart timeout everytime we get a dribble of data?
            rem = self.time_start + self.timeout - time.time()
            if rem <= 0: raise TimeoutError, 'Timeout'
            self.s.settimeout(rem)
        buf = f.read(count - len(res))
        if not buf:
          raise IncompleteReplyError, 'incomplete reply - %d of %d read' % (len(res),count)
        res += buf
      return res

    def processTCPReply(self):
        if self.timeout > 0:
            self.s.settimeout(self.timeout)
        else:
            self.s.settimeout(None)
        f = self.s.makefile('rb')
        try:
          header = self._readall(f,2)
          count = Lib.unpack16bit(header)
          self.reply = self._readall(f,count)
        finally: f.close()
        self.time_finish=time.time()
        self.args['server']=self.ns
        return self.processReply()

    def processReply(self):
        self.args['elapsed']=(self.time_finish-self.time_start)*1000
        u = Lib.Munpacker(self.reply)
        r=Lib.DnsResult(u,self.args)
        r.args=self.args
        #self.args=None  # mark this DnsRequest object as used.
        return r
        #### TODO TODO TODO ####
#        if protocol == 'tcp' and qtype == Type.AXFR:
#            while 1:
#                header = f.read(2)
#                if len(header) < 2:
#                    print '========== EOF =========='
#                    break
#                count = Lib.unpack16bit(header)
#                if not count:
#                    print '========== ZERO COUNT =========='
#                    break
#                print '========== NEXT =========='
#                reply = f.read(count)
#                if len(reply) != count:
#                    print '*** Incomplete reply ***'
#                    break
#                u = Lib.Munpacker(reply)
#                Lib.dumpM(u)

    def getSource(self):
        "Pick random source port to avoid DNS cache poisoning attack."
        while True:
            try:
                source_port = random.randint(1024,65535)
                self.s.bind(('', source_port))
                break
            except socket.error, msg:
                # Error 98, 'Address already in use'
                if msg[0] != 98: raise

    def conn(self):
        self.getSource()
        self.s.connect((self.ns,self.port))

    def req(self,*name,**args):
        " needs a refactoring "
        self.argparse(name,args)
        #if not self.args:
        #    raise ArgumentError, 'reinitialize request before reuse'
        protocol = self.args['protocol']
        self.port = self.args['port']
        self.tid = random.randint(0,65535)
        self.timeout = self.args['timeout'];
        opcode = self.args['opcode']
        rd = self.args['rd']
        server=self.args['server']
        if type(self.args['qtype']) == types.StringType:
            try:
                qtype = getattr(Type, string.upper(self.args['qtype']))
            except AttributeError:
                raise ArgumentError, 'unknown query type'
        else:
            qtype=self.args['qtype']
        if not self.args.has_key('name'):
            print self.args
            raise ArgumentError, 'nothing to lookup'
        qname = self.args['name']
        if qtype == Type.AXFR and protocol != 'tcp':
            print 'Query type AXFR, protocol forced to TCP'
            protocol = 'tcp'
        #print 'QTYPE %d(%s)' % (qtype, Type.typestr(qtype))
        m = Lib.Mpacker()
        # jesus. keywords and default args would be good. TODO.
        m.addHeader(self.tid,
              0, opcode, 0, 0, rd, 0, 0, 0,
              1, 0, 0, 0)
        m.addQuestion(qname, qtype, Class.IN)
        self.request = m.getbuf()
        try:
            if protocol == 'udp':
                self.sendUDPRequest(server)
            else:
                self.sendTCPRequest(server)
        except socket.error, reason:
            raise SocketError, reason
        if self.async:
            return None
        else:
            return self.response

    def sendUDPRequest(self, server):
        "refactor me"
        first_socket_error = None
        self.response=None
        for self.ns in server:
            #print "trying udp",self.ns
            try:
                if self.ns.count(':'):
                    if hasattr(socket,'has_ipv6') and socket.has_ipv6:
                        self.socketInit(socket.AF_INET6, socket.SOCK_DGRAM)
                    else: continue
                else:
                    self.socketInit(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    # TODO. Handle timeouts &c correctly (RFC)
                    self.time_start=time.time()
                    self.conn()
                    if not self.async:
                        self.s.send(self.request)
                        r=self.processUDPReply()
                        # Since we bind to the source port and connect to the
                        # destination port, we don't need to check that here,
                        # but do make sure it's actually a DNS request that the
                        # packet is in reply to.
                        while r.header['id'] != self.tid        \
                                or self.from_address[1] != self.port:
                            r=self.processUDPReply()
                        self.response = r
                        # FIXME: check waiting async queries
                finally:
                    if not self.async:
                        self.s.close()
            except socket.error, e:
                # Keep trying more nameservers, but preserve the first error
                # that occurred so it can be reraised in case none of the
                # servers worked:
                first_socket_error = first_socket_error or e
                continue
        if not self.response and first_socket_error:
            raise first_socket_error

    def sendTCPRequest(self, server):
        " do the work of sending a TCP request "
        first_socket_error = None
        self.response=None
        for self.ns in server:
            #print "trying tcp",self.ns
            try:
                if self.ns.count(':'):
                    if hasattr(socket,'has_ipv6') and socket.has_ipv6:
                        self.socketInit(socket.AF_INET6, socket.SOCK_STREAM)
                    else: continue
                else:
                    self.socketInit(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    # TODO. Handle timeouts &c correctly (RFC)
                    self.time_start=time.time()
                    self.conn()
                    buf = Lib.pack16bit(len(self.request))+self.request
                    # Keep server from making sendall hang
                    self.s.setblocking(0)
                    # FIXME: throws WOULDBLOCK if request too large to fit in
                    # system buffer
                    self.s.sendall(buf)
                    # SHUT_WR breaks blocking IO with google DNS (8.8.8.8)
                    #self.s.shutdown(socket.SHUT_WR)
                    r=self.processTCPReply()
                    if r.header['id'] == self.tid:
                        self.response = r
                        break
                finally:
                    self.s.close()
            except socket.error, e:
                first_socket_error = first_socket_error or e
                continue
        if not self.response and first_socket_error:
            raise first_socket_error

#class DnsAsyncRequest(DnsRequest):
class DnsAsyncRequest(DnsRequest,asyncore.dispatcher_with_send):
    " an asynchronous request object. out of date, probably broken "
    def __init__(self,*name,**args):
        DnsRequest.__init__(self, *name, **args)
        # XXX todo
        if args.has_key('done') and args['done']:
            self.donefunc=args['done']
        else:
            self.donefunc=self.showResult
        #self.realinit(name,args) # XXX todo
        self.async=1
    def conn(self):
        self.getSource()
        self.connect((self.ns,self.port))
        self.time_start=time.time()
        if self.args.has_key('start') and self.args['start']:
            asyncore.dispatcher.go(self)
    def socketInit(self,a,b):
        self.create_socket(a,b)
        asyncore.dispatcher.__init__(self)
        self.s=self
    def handle_read(self):
        if self.args['protocol'] == 'udp':
            self.response=self.processUDPReply()
            if self.donefunc:
                apply(self.donefunc,(self,))
    def handle_connect(self):
        self.send(self.request)
    def handle_write(self):
        pass
    def showResult(self,*s):
        self.response.show()


# Google's public name servers are 8.8.8.8 and 8.8.4.4 for IPv4, and
# 2001:4860:4860::8888 and 2001:4860:4860::8844 for IPv6.
reqobj = DNS.Request(server="192.168.0.1")


def main(cfg_file):
    dns_server_db = read_config_file(cfg_file)
    verify_nameservers(dns_server_db)


def read_config_file(filename):
    """This subroutine opens file filename, which is a JSON
    file, and reads it into a list.  The data structure
    is described above"""

    with open(filename, "r") as fp:
        dns_server_db_list = json.load(fp)
    return dns_server_db_list


def verify_nameservers(dns_server_list):
    """This subroutine iterates over the the
    list of nameservers and tests each one """

    for ns in dns_server_list:
        verify_nameserver(ns)


def verify_nameserver(ns_ut):
    """This method gets a nameserver, loops
    over all of the tests that nameserver
    has to do.
    ns_ut is the nameserver under test.
    """
    if isinstance(ns_ut, dict):
        verify_nameserver_call(ns_ut)
    elif isinstance(ns_ut, list):
        for ns in ns_ut:
            assert isinstance(ns, dict), str(
                ns) + "should be a dict, but its a" + \
                                         str(type(ns_ut)) + " instead"
            verify_nameserver_call(ns)
    else:
        raise ValueError("Was expecting either dict or a list of dicts, "
                         "but got a " + str(type(ns_ut)) + " instead")


def extract_list_of_data(ans):
    """

    :param ans: a DnsResult object from a call to DNS.req
    :return: a list of data from the ans object
    """
    data_list = []
    for a in ans.answers:
        data_list.append(a['data'])
    return data_list


def verify_nameserver_call(key):
    """This method is what actually does the heavy lifting.
    It breaks appart the key to get

    """
    nameserver = key["nameserver"].encode('ascii')
    qtype = key.get("qtype", "A").encode('ascii')
    name = key["name"].encode('ascii')
    nominal = key["nominal"].encode('ascii')
    comment = key.get("comment", "").encode('ascii')
    try:
        answer = reqobj.req(qtype=qtype, server=nameserver, name=name)
    except DNS.Base.TimeoutError as d:
        log_fail(nameserver, qtype, name, "Timed out: " + str(d) + ", comment")
    else:
        data_list = extract_list_of_data(answer)
        failure = answer.header['status'] != "NOERROR"
        if failure:
            log_fail(nameserver, qtype, name, answer.header['status'], comment)
        elif nominal not in data_list:
            log_fail(nameserver, qtype, name,
                     "%s not in %s" % (nominal, data_list), comment)
        else:
            log_success(nameserver, qtype, name, data_list, comment)


def log_fail(nameserver, qtype, name, status, comment=""):
    print("nameserver %s FAILED to lookup %s of %s " %
          (nameserver, qtype, name), "status is %s  %s " % (status, comment))


def log_success(nameserver, qtype, name, d_lst, comment=""):
    print("nameserver %s successfully looked up %s of %s" % (nameserver,
                                                             qtype, name),
          " and got %s | %s " % (d_lst, comment))


if "__main__" == __name__:
    config_filename = sys.argv[1]
    while True:
        try:
            main(config_filename)
        except KeyboardInterrupt:
            print("Got control-C")
            sys.exit(1)
        # This will handle any exception so be carefull with it
        except Exception as e:
            print("Got an exception we didn't plan for %s " % str(e))
            traceback.print_exc()
            sys.exit(2)

