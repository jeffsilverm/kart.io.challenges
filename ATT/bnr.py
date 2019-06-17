#! /usr/bin/python3
#
import datetime
import os
import sys
import time

LOG_FILE = "bnr.log"
DELAY = 10  # Seconds
delay = datetime.timedelta(seconds=DELAY)


def log(string):
    print(datetime.datetime.utcnow(), string, file=sys.stderr)


def run_bnr(s: str) -> None:
    with open(LOG_FILE, "a") as f:
        print(f"{s} Running bnr! at {datetime.datetime.utcnow()}", file=f)


if "__main__" == __name__:
    now = datetime.datetime.now(datetime.timezone.utc)
    log(f"starting at {str(now)}")
    if os.path.exists(LOG_FILE) and os.path.isfile(LOG_FILE):
        statbuf = os.stat(LOG_FILE)
        last_run_time: datetime.datetime = datetime.datetime.fromtimestamp(
            statbuf.st_mtime, datetime.timezone.utc)
        log(f"The last time {LOG_FILE} was modified was {last_run_time}")
        if now - last_run_time < delay:
            delay_flt: float = (delay + (now - last_run_time)).total_seconds()
            log(f"Sleeping {delay_flt} seconds before running")
            time.sleep(delay_flt)
        else:
            log(f"Resuming without delay!")
        run_bnr("Resuming")
    else:
        log(f"file {LOG_FILE} is being created")
        run_bnr("Beginning")
    delay_flt: float = delay.total_seconds()
    while True:
        log(f"getting ready to sleep for {delay_flt} seconds")
        time.sleep(delay_flt)
        run_bnr("Continuing")
