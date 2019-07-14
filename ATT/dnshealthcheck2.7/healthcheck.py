#! /usr/bin/env python
#
# This program deos a variety of health checks
#
#
from __future__ import print_function

import datetime
import os
import subprocess
import sys

COMMUNITY_NAME = "public"  # Poor practice - don't hard code community strings
WIAR = "Working in all respects"
inst_lc = 1  # Line counter for instruction file


class Logger(object):
    """This class implements a simple logger """

    def __init__(self, logfile, hostname):
        assert isinstance(logfile, file), "logfile should be type 'file' but" \
                                          "but is really %s" % str(
            type(logfile))
        self.logfile = logfile
        self.hostname = hostname


class Checker(object):
    global inst_lc

    def __init__(self, logger_filename, inst_filename, my_fqdn):
        if os.path.isfile(logger_filename):
            print("File %s already exists - exiting" % logger_filename)
            sys.exit(1)
        self.logfile = open(logger_filename, "w")
        self.hostname = my_fqdn
        self.inst_filename = inst_filename  # For documentation purposes
        print("||| %s %s %s" % (self.hostname,
                                datetime.datetime.now().__str__(), my_fqdn),
              file=self.logfile)
        # The keys to this dictionary are the instruction codes
        # The values of this dictionary are lists of tests.
        # An element of this list is the instruction code followed by:
        # error level (SUCCESS, FAILURE, WARNING)
        # a comment
        # and the parameters
        self.report_dict = dict()

    def append(self, key, err_level, comment ):
        entry = (err_level, comment)
        if key in self.report_dict:
            self.report_dict[key]=[entry]
        else:
            self.report_dict[key].append(entry)

    def logit(self, inst, status, command, message):
        error_level_str = \
            ("SUCCESS: " if status == 0 else (
                "WARNING: " if status == 99999 else "FAIL:"))
        print(
            "*** {}`` {}``  {}``  ({:d})`` ".format(
                error_level_str,
                self.hostname, self.inst_filename,
                inst_lc), 50 * "*", "\n>>> %s " % " ".join(command),
            "\n", message, "\n", file=self.logfile)

    def check_dns(self, params):
        """This method does a DNS check"""
        print("in check_dns: parameters are: ", params, file=sys.stderr)

        args = ['dig']
        # Handle the server argument, if there is one
        if params[0] != "" and params[0] is not None:
            args.append("@" + params[0])
        args.append(params[1])  # target name
        args.extend(["-t", params[2]])  # qtype
        try:
            results = subprocess.check_output(args)
        except subprocess.CalledProcessError as p:
            status = p.returncode
            results = ""
        else:
            status = 0
        self.logit(status=status, message=results, command=args)

    def check_ping(self, params):
        """This method does a ping check"""
        print("in check_ping: parameters are: ", params, file=sys.stderr)
        cmd = "ping6" if ":" in params[0] else "ping4"
        args = [cmd, params[0], "-c", "10"]
        try:
            results = subprocess.check_output(args)
        except subprocess.CalledProcessError as p:
            status = p.returncode
            results = ""
        else:
            status = 0
        self.logit(inst="PING", status=status, message=results, command=args)

    def check_ntp(self, params):
        """This method does a check on NTP"""
        print("in check_ntp: parameters are: ", params, file=sys.stderr)
        args = ["ntpq", "-p", "-n"]
        try:
            results = subprocess.check_output(args)
        except subprocess.CalledProcessError as p:
            status = p.returncode
            results = ""
            comment = "Running ntpq caused a CalledProcessError exception to be raised"
        else:
            status = 0
            comment = WIAR
        self.logit(inst="NTP", status=status, message=results, command=args)

    def check_snmp(self, cn, params):
        """This method checks SNMP"""
        # Note that the community name is not printed out as it is sensitive
        print("in check_snmp: parameters are: ", params, file=sys.stderr)
        args = ['snmpget', '-v2c', '-c', cn, params[0], params[1]]
        try:
            results = subprocess.check_call(args)
        except subprocess.CalledProcessError as p:
            status = p.returncode
            results = ""
            comment = \
                "The snmpget command returned code %s and no other results" %\
                status
            error_level = "FAIL"
        else:
            status = 0
            comment = WIAR
            error_level = "PASS"
        args[3] = "XXXX"

        self.logit(inst="SNMP", status=status, command=" ".join(args),
                   message=results)
        # error level (SUCCESS, FAILURE, WARNING)
        # a comment
        # and the parameters
        self.append('SNMP', error_level, comment )

    def report_generator(self):
        """
        This method generates a nicely formatted report.  The first column is
        the test.  The second column is the result (PASS, FAIL, WARN).  The
        third column is a comment
        :return:
        """
        keys = ['PING','SNMP','NTP','DNS']
        for k in keys:
            if k not in self.report_dict:
                assert KeyError, "key %s is not in the report_dict"
        for k in self.report_dict.keys():
            if k not in keys:
                assert KeyError,\
                    "key %s is not in the list of keys in the report generator"
        WIDTH=132
        line=[]
        line[0]="+------+--------+----------------------------------------- "
        line[1]="| Test | Result | Comments"
        line[2]=line[0]
        for key in ['PING','SNMP','NTP','DNS']:
            for test in self.report_dict[key]




def get_my_fqdn():
    """Return the fully qualified domain name of this machine."""

    # Although the documentation says that there are ways to get the FQDN using
    # socket or os.uname, they don't always return FQDNs.
    # For that matter, neither does the hostname command.
    ret = subprocess.check_output(["hostname", "-f"])
    return ret.rstrip()


def main(args):
    """This method opens a file of instructions, and a raw output file,"""

    global COMMUNITY_NAME
    global inst_lc

    my_fqdn = get_my_fqdn()
    inst_file = open(args[1], "r")
    checker = Checker(logger_filename=sys.argv[2], inst_filename=sys.argv[1],
                      my_fqdn=my_fqdn)

    for instruction in inst_file.readlines():
        parameters = instruction.rstrip().split("\t")
        inst = parameters.pop(0)
        if inst == "DNS":
            checker.check_dns(parameters)
        elif inst == "PING":
            checker.check_ping(parameters)
        elif inst == "NTP":
            checker.check_ntp(parameters)
        elif inst == "SNMP":
            checker.check_snmp(COMMUNITY_NAME, parameters)
        else:
            print("bad instruction: %s, continuing" % inst, file=sys.stderr)
        inst_lc += 1


if "__main__" == __name__:
    main(sys.argv)
