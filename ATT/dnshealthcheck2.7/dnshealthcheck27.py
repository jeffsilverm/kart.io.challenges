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

# I got pydns from SourceForge
# https://sourceforge.net/projects/pydns/files/latest/download     # noqa

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
