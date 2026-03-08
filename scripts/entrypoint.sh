#!/bin/bash

usage="$(basename "$0") [-h] [--debug] [--logs] [--no-server] [--server] [--bt-studio] \n\n

optional arguments:\n
\t  -h  show this help message and exit\n
\t  --debug run bash inside RADI\n
\t  --logs record logs and run RADI\n
\t  --no-server run RADI without webserver
\t  --server run RADI with webserver
\t  --bt-studio run BT Studio"

debug=false
log=false
webserver=true
btstudio=false

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
    btstudio=false
    ;;
  -s | --server )
    webserver=true
    btstudio=false
    ;;
  -bt | --bt-studio )
    btstudio=true
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

if [ $btstudio == true ]; then
    runserver="python3 /BtStudio/manage.py runserver 0.0.0.0:7164"
else
    runserver=""
fi

if [ $webserver == true ]; then
    runserver="python3 /RoboticsAcademy/manage.py runserver 0.0.0.0:7164"
fi

if [ -d "/RoboticsApplicationManager" ]; then
  runram="python3 RoboticsApplicationManager/robotics_application_manager/manager/manager.py 0.0.0.0 7163"
else
  # TODO: check for updates
  source check_ram_version.sh
  runram="python3 /ram_entrypoint.py 0.0.0.0 7163"
fi

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
