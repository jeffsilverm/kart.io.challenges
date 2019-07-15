#! /usr/bin/env python
#
# This program deos a variety of health checks
#
#
from __future__ import print_function

# The following line comes from
# https://gist.github.com/pylover/7870c235867cf22817ac5b096defb768
# noinspection PyCompatibility
import builtins  # noqa
import datetime
import os
import stat
import subprocess
import sys
import traceback

# If the following import fails, then use pip to install package future

COMMUNITY_NAME = "public"  # Poor practice - don't hard code community strings
WIAR = "Working in all respects"
WARNING = 99999
inst_lc = 1  # Line counter for instruction file


class Logger(object):
    """This class implements a simple logger """

    def __init__(self, logfile, hostname):
        assert isinstance(logfile,
                          builtins.file), "logfile should be type 'file' but" \
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
        self.lc = 0
        self.comment = ""

    def append(self, key, err_level, message) -> None:
        """

        :rtype: None
        """
        entry = (err_level, message)
        if key in self.report_dict:
            self.report_dict[key].append(entry)
        else:
            self.report_dict[key] = [entry]

    def record_lc(self, lc, comment=""):
        """This records the instruction file line counter and the comment"""
        self.lc = lc
        self.comment = comment

    def logit(self, inst, status, command, message, results) -> None:
        error_level_str = \
            ("SUCCESS: " if status == 0 else (
                "WARNING: " if status == WARNING else "FAIL:"))  # type: str
        if isinstance(results, str):
            results_str = results
        else:
            # results is a byte array and it does not render \n properly.
            results_str = results.decode("ascii")
        print(
            "*** ``{}`` {}``  {}``  ({}:{:d})`` ".format(
                inst, error_level_str,
                self.hostname, self.inst_filename, self.lc,
                inst_lc), 50 * "*", "\n>>> %s " % " ".join(command),
            "\n", message, "\n", self.comment, file=self.logfile)
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
        if len(params) > 2:
            args.extend(["-t", params[2]])  # qtype
        else:
            args.extend(["-t", "A"])
        try:
            results = subprocess.check_output(args)
        except subprocess.CalledProcessError as p:
            status = p.returncode
            results = ""
            message = "FAIL: dns check failed because " \
                      "subprocess.check_output raised a {} exception".format(
                         str(p))
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

    @staticmethod
    def get_file_attrs(filename):
        """This function returns the uid, gid, and mode of the file
        :type filename: str
        :returns    tuple   int, int, int   UID, GID, mode
        """

        st = os.stat(filename)
        uid = st.st_uid
        gid = st.st_gid
        mode = stat.S_IMODE(st.st_mode)
        return uid, gid, mode

    def check_file(self, params):
        """Check that a file is protected properly and is owned properly"""

        results = b""  # Since this routine doesn't invoke any commands. there
        # no results
        args = [""]

        try:
            (uid, gid, mode) = self.get_file_attrs(params[0])
        except Exception as e:
            status = 1
            message = "FAIL: os.stat method raised an exception %s" % str(e)
        else:
            nom_uid = (
                int(params[1]) if isinstance(params[1], str) else params[1])
            nom_gid = (
                int(params[2]) if isinstance(params[2], str) else params[2])
            nom_mode = (
                int(params[3], base=8) if isinstance(params[3], str) else
                params[2])
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
                mode_ok = "WRONG: mode is %o should be %o " % (mode, nom_mode)
                status = WARNING
            message = uid_ok + gid_ok + mode_ok
        self.logit(inst="FILE", status=status, command=args,
                   message=message, results=results)
        return status, message

    def check_erc(self, params):
        """This checks the file /etc/resolv.conf """

        # I decided to test /etc/resolv.conf as a file in a separate test
        # (  status, message ) = self.check_file(params)
        message = "FAIL: bad %s file: no 'nameserver' lines were found" % \
                  params[0]
        try:
            ercf = open(params[0], "r")
            lines = ercf.readlines()
            ercf.close()
        except Exception as e:
            message = "FAIL: reading the file %s raised an exception %s" % \
                      (params[0], str(e))
            self.logit(inst="ERC", status=0,
                       command=[],
                       message=message,
                       results=b"")
        else:
            for l in lines:
                elements = l.split()
                if len(elements) > 0 and "nameserver" == elements[0]:
                    ipaddr = elements[1]
                    message = "DNS test on server %s with host %s" % \
                              (ipaddr, params[2])
                    self.logit(inst="ERC", status=0,
                               command=['dig', '@' + ipaddr, params[2]],
                               message=message,
                               results=b"See below")
                    self.check_dns(params)

            # There is a fundamental design flaw in this program I am not
            # going to fix now - the check_XXX methods should return the test
            # results so that one method can call another.
        if "FAIL" in message:
            status = 1
        else:
            status = 0
        return status

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
        args[3] = "XXXX"  # str

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

    def close_log_file(self):
        print("ENDENDENDEND\n", file=self.logfile)
        self.logfile.close()


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
    try:
        for instruction in inst_file.readlines():  # type: str
            if instruction == "\n":
                print("Came to an empty line in %s" % sys.argv[1],
                      file=sys.stderr)
                continue
            parameters = instruction.rstrip().split("\t")
            # Is there a comment in the last column?  It begins with # if so
            if parameters[-1][0] == "#":
                comment = parameters[-1]
                parameters = parameters[0:-1]
            else:
                comment = ""
            checker.record_lc(inst_lc, comment)
            inst = parameters.pop(0)
            if inst == "DNS":
                checker.check_dns(parameters)
            elif inst == "PING":
                checker.check_ping(parameters)
            elif inst == "NTP":
                checker.check_ntp(parameters)
            elif inst == "SNMP":
                checker.check_snmp(COMMUNITY_NAME, parameters)
            elif inst == "FILE":
                checker.check_file(parameters)
            elif inst == "ERC":
                checker.check_erc(parameters)
            else:
                print("bad instruction: %s, continuing" % inst, file=sys.stderr)
            inst_lc += 1
        checker.close_log_file()
    except Exception as e:
        print("Raised an exception at line %d in the instruction file\n" %
              checker.lc, "comment is %s\n" % checker.comment,
              str(e), traceback.print_exc(),
              file=sys.stderr)


if "__main__" == __name__:
    main(sys.argv)
