#! /usr/bin/python3
#
# logrator.py - a demonstration logrotator
# This python script runs the logrator command with the selected
# logrotate.conf file

import datetime
import glob
import os
import subprocess
import sys
import time
import random

print(f"logrotator.py is starting.  PID is {os.getpid()}")
PWD = os.getcwd()
LOGFILE = ["--log", f"{PWD}/logrotate_log"]
CONFIGFILES = f"{PWD}/one.config"  # docs say more than one conf file allowed
APP_LOG_FILENAME = f"{PWD}/my_logfile.log"
DELAY = 5  # seconds
# Comment out for no force.  Force tells logrotate to rotate the files
# even if it thinks it is not necessary
FORCE = "--force"
#
STATEFILE = f"{PWD}/logrotate_state_file"
ITERATIONS = 12
ROTATIONS = 8

with open(CONFIGFILES, "w") as cf:
    configuration = (
        "# sample logrotate configuration file\n"
        "compress\n"
        f"{APP_LOG_FILENAME} "
        "{\nhourly\n"
        f"rotate {ROTATIONS}\n"
        "nomissingok\n"
        # "postrotate\n"
        # "\techo 'After logfile rotation'\n"
        # f"\tls -lort {APP_LOG_FILENAME}\n"
        # "endscript\n"
        "}\n"
    )
    cf.writelines(configuration)

for i in range(1, ITERATIONS):
    now = str(datetime.datetime.now())
    print(f"##### iteration {i} {now}", file=sys.stderr)
    with open(APP_LOG_FILENAME, "a") as a:
        a.write(now)
        a.writelines("|||" * random.randint(1, 6000))
    try:
        logrotate_return: subprocess.CompletedProcess = subprocess.run(
            ["/usr/sbin/logrotate", "-s", STATEFILE, FORCE] +
            # LOGFILE is a 2 element list
            LOGFILE + [CONFIGFILES],
            # If the subprocess terminates abnormally, then raise an exception
            check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print(logrotate_return, file=sys.stderr)
    except subprocess.CalledProcessError as c:
        print("logrotate died a horrible death", c, file=sys.stderr)
    logfile_list = glob.glob(APP_LOG_FILENAME + "*", recursive=False)
    logfile_list.sort()
    for lf in logfile_list:
        ts = os.stat(lf).st_mtime
        fsz = os.stat(lf).st_size
        dt_ts = datetime.datetime.utcfromtimestamp(ts)
        ts_str = dt_ts.strftime('%Y-%m-%d %H:%M:%S')
        print(f"File: {lf} mtime {ts_str} size {fsz} bytes")
    time.sleep(DELAY)


print("logrotator.py exiting normally" + str(datetime.datetime.now()),
      file=sys.stderr)


# To make this thing unstoppable, consider the following:
"""
jeffs@jeffs-desktop:/home/jeffs/work/ATT/logrotate  (development) *  $ cat ~/.config/systemd/user.control/logrotator.service    # noqa
# unit file for the logrotator

[Unit]
Description=A log rotator demo

[Service]
Type=simple
ExecStart=python3 /home/jeffs/work/ATT/logrotate/logrotator.py
Restart=always


jeffs@jeffs-desktop:/home/jeffs/work/ATT/logrotate  (development) *  $ 

"""

"""
# Start it with
# systemctl --user start logrotator     
#
# check on it with
# systemctl --user status logrotator    
#
# Stop it with
# systemctl --user stop logrotator      
"""
# NOTE this only works in my environment, you'll have to customize for yours
"""
journalctl --user --since="2019-06-25" --unit=logrotator
or perhaps
journalctl --user --follow --unit=logrotator

"""
