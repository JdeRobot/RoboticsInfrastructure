#!/bin/bash

usage="$(basename "$0") [-h] [--debug] [--logs] [--no-server]\n\n

optional arguments:\n
\t  -h  show this help message and exit\n
\t  --debug run bash inside RADI\n
\t  --logs record logs and run RADI\n
\t  --no-server run RADI without webserver"

debug=false
log=false
webserver=true

while [[ "$1" =~ ^- && ! "$1" == "--" ]]; do case $1 in
  -h | --help )
    echo -e $usage
    exit
    ;;
  -d | --debug )
    shift; debug=true
    ;;
  -l | --logs )
    shift; log=true
    ;;
  -ns | --no-server )
    webserver=false
    ;;
esac; shift; done
if [[ "$1" == '--' ]]; then shift; fi

# If DRI_NAME is empty, run set_dri_name to try and set it automatically
if [ -z "${DRI_NAME}" ]; then
    source set_dri_name.sh
fi

if [ $webserver == true ]; then
    runserver="python3 /RoboticsAcademy/manage.py runserver 0.0.0.0:7164"
else
    runserver=""
fi

runmanager="python3 RoboticsAcademy/manager/manager.py"
runram="python3 RoboticsAcademy/src/manager/manager/manager.py 0.0.0.0 7163"
root="cd /"

# TEST LOGS
if [ $log == true ]; then
    DATE_TIME=$(date +%F-%H-%M) # FORMAT year-month-date-hours-mins
    mkdir -p /root/.roboticsacademy/log/$DATE_TIME/
    script -q -c "$root & $runserver & $runram ;" /root/.roboticsacademy/log/$DATE_TIME/manager.log
    cp -r /root/.ros/log/* /root/.roboticsacademy/log/$DATE_TIME
else
    if [ $debug == true ]; then
      { bash ; }
    else
      { $root & $runserver & $runram ; }
    fi
fi
