#! /usr/bin/env python
#
# This program deos a variety of health checks
#
#
from __future__ import print_function

import datetime
import os
import stat
import subprocess
import sys

# If the following import fails, then use pip to install package future

COMMUNITY_NAME = "public"  # Poor practice - don't hard code community strings
WIAR = "Working in all respects"
WARNING = 99999
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
        # if os.path.isfile(logger_filename):
        #    # print("File %s already exists - do you want to overwrite?" %
        #    # logger_filename)
        #    ans = input("File %s already exists - do you want to "
        #                "overwrite it? " % logger_filename)
        #    if ans != "y" and ans != "Y" and ans != "YES" or ans != "yes":
        #        sys.exit(1)
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
        # a message
        # and the parameters
        self.report_dict = dict()

    def append(self, key, err_level, message):
        """

        :rtype: None
        """
        entry = (err_level, message)
        if key in self.report_dict:
            self.report_dict[key] = [entry]
        else:
            self.report_dict[key].append(entry)

    def logit(self, inst, status, command, message, results) -> None:
        error_level_str = \
            ("SUCCESS: " if status == 0 else (
                "WARNING: " if status == WARNING else "FAIL:"))  # type: str
        # results is a byte array and it does not render \n properly.
        results_str = results.decode("ascii")
        print(
            "*** {}`` {}``  {}``  ({})`` ".format(
                inst, error_level_str,
                self.hostname, self.inst_filename,
                inst_lc), 50 * "*", "\n>>> %s " % " ".join(command),
            "\n", message, "\n", file=self.logfile)
        print(results_str, file=self.logfile)
        self.logfile.flush()

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
            message = "FAIL: dns check failed because " \
                      "subprocess.check_output raised a %s exception" % str(p)
        else:
            status = 0
            message = "PASS"
        self.logit(inst="DNS", status=status, message=message, command=args,
                   results=results)

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
            message = "FAIL: ping check failed because " \
                      "subprocess.check_output raised a %s exception" % str(p)
        else:
            status = 0
            message = "PASS"
        self.logit(inst="PING", status=status, message=message, command=args,
                   results=results)

    def check_ntp(self, params):
        """This method does a check on NTP"""
        print("in check_ntp: parameters are: ", params, file=sys.stderr)
        args = ["ntpq", "-p", "-n"]
        try:
            results = subprocess.check_output(args)
        except subprocess.CalledProcessError as p:
            status = p.returncode
            results = ""
            message = "Running ntpq caused a CalledProcessError exception to " \
                      "be raised"
        else:
            status = 0
            message = WIAR
            # There is a more sophisticated test that NTP is working
            # properly, IMPLEMENT THAT LATER!!!!
        self.logit(inst="NTP", status=status, message=message, results=results,
                   command=args)

    def check_file(self, params):
        """Check that a file is protected properly and is owned properly"""
        nom_uid = (int(params[1]) if isinstance(params[1], str) else params[1])
        nom_gid = (int(params[2]) if isinstance(params[2], str) else params[2])
        nom_mode = (int(params[3], base=8) if isinstance(params[3], str) else
                    params[2])
        results = b""
        try:
            st = os.stat(params[0])
        except Exception as e:
            status = 1
            message = "FAIL: os.stat method raised an exception %s" % str(e)
        else:
            uid = st.st_uid
            gid = st.st_gid
            mode = stat.S_IMODE(st.st_mode)
            status = 0
            if uid == params[1]:
                uid_ok = "UID OK %d " % uid
            else:
                uid_ok = "WARNING: UID is %d should be %d " % \
                         (uid, nom_uid)
                status = WARNING
            if gid == nom_gid:
                gid_ok = "GID OK %d " % nom_gid
            else:
                gid_ok = "WARNING: GID is %d should be %d" % \
                         (gid, nom_gid)
                status = WARNING
            if mode == nom_mode:
                # Note that the output of the oct function is a string -
                # easier for
                # humans to see ints in oct
                mode_ok = "MODE OK"
            else:
                mode_ok = "WRONG: mode is %o should be %s " % (mode,
                                                               oct(params[3]))
                status = WARNING
            message = uid_ok + gid_ok + mode_ok
        self.logit(inst="FILE", status=status, command="",
                   message=message, results=results)

    def check_snmp(self, cn, params):
        """This method checks SNMP"""
        # Note that the community name is not printed out as it is sensitive
        print("in check_snmp: parameters are: ", params, file=sys.stderr)
        args = ['snmpget', '-v2c', '-c', cn, params[0], params[1]]
        try:
            results = subprocess.check_output(args)
        except subprocess.CalledProcessError as p:
            status = p.returncode
            results = ""
            message = \
                "The snmpget command returned code %s and no other results" % \
                status
            error_level = "FAIL"
        else:
            status = 0
            message = WIAR
            error_level = "PASS"
        # hide the community name string
        args[3] = "XXXX"

        self.logit(inst="SNMP", status=status, command=args,
                   message=message, results=results)
        # error level (SUCCESS, FAILURE, WARNING)
        # a message
        # and the parameters
        self.append('SNMP', error_level, message)

    def report_generator(self):
        """
        This method generates a nicely formatted report.  The first column is
        the test.  The second column is the result (PASS, FAIL, WARN).  The
        third column is a message
        :rtype: object
        :return:
        """
        keys = ['PING', 'SNMP', 'NTP', 'DNS']
        for k in keys:
            if k not in self.report_dict:
                assert KeyError, "key %s is not in the report_dict"
        for k in self.report_dict.keys():
            if k not in keys:
                assert KeyError, \
                    "key %s is not in the list of keys in the report generator"

        line = []
        line[0] = "+------+--------+----------------------------------------- "
        line[1] = "| Test | Result | Comments"
        line[2] = line[0]
        for key in ['PING', 'SNMP', 'NTP', 'DNS']:
            for test in self.report_dict[key]:
                assert test in self.report_generator()
                raise NotImplemented


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

    for instruction in inst_file.readlines():  # type: str
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
