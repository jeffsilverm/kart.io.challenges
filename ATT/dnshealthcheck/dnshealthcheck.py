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
from typing import List, Union

# I got pydns from SourceForge
# https://sourceforge.net/projects/pydns/files/latest/download     # noqa
# As of 5-July-2019, it was version 3.2.0
import DNS

reqobj = DNS.Request(server="192.168.0.1")


def main(cfg_file: str):
    dns_server_db = read_config_file(cfg_file)
    verify_nameservers(dns_server_db)


def read_config_file(filename: str) -> List:
    """This subroutine opens file filename, which is a JSON
    file, and reads it into a list.  The data structure
    is described above"""

    with open(filename, "r") as fp:
        dns_server_db_list: List = json.load(fp)
    return dns_server_db_list


def verify_nameservers(dns_server_list: list) -> None:
    """This subroutine iterates over the the
    list of nameservers and tests each one """

    for ns in dns_server_list:
        verify_nameserver(ns)


def verify_nameserver(ns_ut: Union[dict, list]) -> None:
    """This method gets a nameserver, loops
    over all of the tests that nameserver
    has to do.
    ns_ut is the nameserver under test.
    """
    if isinstance(ns_ut, dict):
        verify_nameserver_call(ns_ut)
    elif isinstance(ns_ut, list):
        for ns in ns_ut:
            assert isinstance(ns, dict), f"{ns} should be a dict, but its a" \
                f" {str(type(ns_ut))} instead"
            verify_nameserver_call(ns)
    else:
        raise ValueError("Was expecting either dict or a list of dicts, "
                         f"but got a {str(type(ns_ut))} instead")


def verify_nameserver_call(key: dict) -> None:
    """This method is what actually does the heavy lifting.
    It breaks appart the key to get

    """
    nameserver = key["nameserver"]
    qtype = key["qtype"]
    name = key["name"]
    nominal = key["nominal"]
    answer = reqobj.req(qtype=qtype, server=nameserver, name=name)
    print(dir(answer), nominal)
    failure = answer.status == "NXDOMAIN"  # This is wrong.  Failure should
    # be when the success string is not seen
    if failure:
        log_fail(nameserver, qtype, name, answer.status)


def log_fail(nameserver, qtype, name, status) -> None:
    print(f"nameserver {nameserver} FAILED to lookup {qtype} of {name} "
          f"status is {status}")


if "__main__" == __name__:
    config_filename = "dns_demo_01.json"
    while True:
        try:
            main(config_filename)
        except KeyboardInterrupt:
            print("Got control-C", file=sys.stderr)
            sys.exit(1)
        # This will handle any exception so be carefull with it
        except Exception as e:
            print(f"Got an exception we didn't plan for {e} ", file=sys.stderr)
            traceback.print_exc()
            sys.exit(2)
