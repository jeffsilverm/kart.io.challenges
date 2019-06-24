#! /bin/bash
#
# logrator.sh - a demonstration logrotator
# This bash script runs the logrator command with the selected
# logrotate.conf file
#
STATEFILE="${PWD}/logrotate_state"
LOGFILE="--log ${PWD}/logrotate_log"
CONFIGFILES="${PWD}/one.config"           # docs say more than one conf file allowed
APP_LOG_FILENAME="${PWD}/my_logfile.log"
DELAY=5 # seconds
# Comment out for no force.  Force tells logrotate to rotate the files 
# even if it thinks it is not necessary
FORCE="--force"
#
STATEFILE="${PWD}/logrotate_state_file"
ITERATIONS=5
ROTATIONS=8

# I found this trick with tee at
# https://stackoverflow.com/questions/4937792/using-variables-inside-a-bash-heredoc
# "Using variables inside a bash heredoc"
tee ${CONFIGFILES} > /dev/null << END
# sample logrotate configuration file
compress

${APP_LOG_FILENAME} {
  hourly
  rotate ${ROTATIONS}
  nomissingok
  postrotate
    echo "After logfile rotation"
    ls -lort ${APP_LOG_FILENAME}*
  endscript
}
END

cat ${CONFIGFILES} 

for i in $(seq 1 ${ITERATIONS} ) ; do
  echo "###### iteration ${i}"
  DATE=$(date +%Y%m%d-%H%M%S) > ${APP_LOG_FILENAME}
  # Give the log file a little bulk
  cat psuedo_random.txt >> ${APP_LOG_FILENAME}
  echo ${DATE} >> ${APP_LOG_FILENAME}
  if ! /usr/sbin/logrotate -s $STATEFILE $LOGFILE $FORCE  $CONFIGFILES ; then
    echo "logrotate exited with ERROR status $?"
    exit 1
  fi
  sleep ${DELAY}
done


