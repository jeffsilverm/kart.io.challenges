#! /usr/bin/python
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
from __future__ import print_function

import json
import random
import string
import subprocess
import sys
import traceback

defaults = {'protocol': 'udp', 'port': 53, 'qtype': 'A', 'rd': True,
            'timing': 1, 'timeout': 30, 'server_rotate': 0, 'server': "localhost"}


def parse_resolv_conf(resolv_path="/etc/resolv.conf"):
    """parses the /etc/resolv.conf file and sets defaults for name servers"""
    global defaults
    lines = open(resolv_path).readlines()
    for line in lines:
        line = string.strip(line)
        if not line or line[0] == ';' or line[0] == '#':
            continue
        fields = string.split(line)
        if len(fields) < 2:
            continue
        if fields[0] == 'domain' and len(fields) > 1:
            defaults['domain'] = fields[1]
        if fields[0] == 'search':
            pass
        if fields[0] == 'options':
            pass
        if fields[0] == 'sortlist':
            pass
        if fields[0] == 'nameserver':
            defaults['server'].append(fields[1])


class DnsRequest:
    """ high level Request object.
     This allows a set of defaults which can change over the course of the
     execution of the program.  You can also have different DnsRequest
     objects for different defaults"""

    def __init__(self, *name, **args):
        self.donefunc = None
        self.defaults = args
        self.argparse(name, args)
        self.tid = 0

    def argparse(self, name, args):

        # Deal with a default name or a list of names
        if not name and 'name' in self.defaults:
            args['name'] = self.defaults['name']
        if isinstance(name, str):
            args['name'] = name
        else:
            if len(name) == 1:
                if name[0]:
                    args['name'] = name[0]
            # Otherwise, hope that the default includes a name
        # This was in the original, to rotate servers.  I might take it out
        # because I don't understand it.
        if defaults['server_rotate'] and \
                isinstance(defaults['server'], list):
            defaults['server'] = defaults['server'][1:] + defaults['server'][:1]
        for i in defaults.keys():
            if not args.has_key(i):
                if self.defaults.has_key(i):
                    args[i] = self.defaults[i]
                else:
                    args[i] = defaults[i]
        # if the server is a string, then convert it to a list of length 1
        if not isinstance(args['server'], str):
            raise ValueError("args[\'server\'] is a {0} not a string".format(
                str(type(args['server']) )))
        self.args = args

    def req(self, *name, **args):
        " needs a refactoring "
        self.argparse(name, args)
        # if not self.args:
        #    raise ArgumentError, 'reinitialize request before reuse'
        use_tcp = self.args['protocol'].lower() == "tcp"
        self.port = self.args['port']
        self.tid = random.randint(0, 65535)
        self.timeout = self.args['timeout']

        use_rd = self.args['rd']  # recursion desired
        server = self.args['server']
        qtype = self.args['qtype']
        if not self.args.has_key('name'):
            print(self.args)
            raise ValueError('nothing to lookup')
        qname = self.args['name']
        if qtype == 'AXFR' and not use_tcp:
            print('Query type AXFR, protocol forced to TCP')
            use_tcp = 'tcp'
        if qtype == 'x':
            log_fail(server, qtype, name, "NOT-IMPLEMENTED",
                     comment="query type -x is not implemented yet")
        tcp = "+tcp" if use_tcp else "+notcp"
        rd = "+recurse" if use_rd else "+norecurse"
        dig_command = ['dig', '@' + server, '-t' + qtype, "+noall", "+answer",
                       rd, tcp, qname]
        try:
            r = subprocess.check_output(args=dig_command)
        except subprocess.CalledProcessError as e:
            print(str(e))
        else:
            # Looking at the length of r is very brittle if the implementation
            # of req changes
            if len(r) > 0:
                # Among other things, strip off the trailing \n
                stdout_lst = [t.split("\t") for t in r[:-1].split('\n')]
                answer_list = [f[6] for f in stdout_lst]
            else:
                answer_list = []
            return answer_list


def main(cfg_file):
    global dns_obj
    dns_server_db = read_config_file(cfg_file)
    dns_obj = DnsRequest()
    verify_nameservers(dns_server_db)


def read_config_file(filename):
    """This subroutine opens file filename, which is a JSON
    file, and reads it into a list.  The data structure
    is described above"""

    with open(filename, "r") as fp:
        dns_server_db_list = json.load(fp)
    # If there is a request that has only one answer, then make it a list
    for dns_server in dns_server_db_list:
        if not isinstance( dns_server["nominal"], list):
            dns_server["nominal"] = [ dns_server["nominal"] ]
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

def nominal_in_answer ( nom, data_lst ):
    """
    Return True if at least one element in nom is equal to at least
    one element in data_lst.
    :param nom:  The nominal answers,
    :param data_lst:
    :return: bool
    """
    for n in nom:
        if n in data_lst:
            return True
    return False

def verify_nameserver_call(key):
    """This method is what actually does the heavy lifting.
    It breaks appart the key to get

    """
    nameserver = key["nameserver"].encode('ascii')
    qtype = key.get("qtype", "A").encode('ascii')
    name = key["name"].encode('ascii')
    nominal = [k.encode('ascii') for k in key["nominal"] ]
    comment = key.get("comment", "").encode('ascii')
    try:
        answer = dns_obj.req(qtype=qtype, server=nameserver, name=name)
    except subprocess.CalledProcessError as e:
        if e.returncode == 9:
            log_fail(nameserver, qtype, name,
                     "Timed out: " + str(e) + ", comment")
    else:
        if answer is None or len(answer) == 0:
            log_fail(nameserver, qtype, name, "returned no answers but didn't raise an exception, either")
        elif not nominal_in_answer(nominal, answer):
            log_fail(nameserver, qtype, name,
                     "%s not in %s" % (nominal, answer), comment)
        else:
            log_success(nameserver, qtype, name, answer, comment)
        """
        # This is left over from when I used the subroutine in pydata.  When
        # I have time, I will use a larger output from dig and extract this 
        # information
        data_list = extract_list_of_data(answer)
        failure = answer.header['status'] != "NOERROR"
        if failure:
            log_fail(nameserver, qtype, name, answer.header['status'], comment)
        elif not nominal_in_answer(nominal, data_list):
            log_fail(nameserver, qtype, name,
                     "%s not in %s" % (nominal, data_list), comment)
        else:
            log_success(nameserver, qtype, name, data_list, comment)
"""

def log_fail(nameserver, qtype, name, status, comment=""):
    print("nameserver %s FAILED to lookup %s of %s " %
          (nameserver, qtype, name), "status is '%s' comment: '%s' " % (status, comment))


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
