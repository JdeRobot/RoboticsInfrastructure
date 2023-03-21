#!/bin/bash

root="cd /"
ros_setup="source /.env && source ~/.bashrc"
runserver="python3 RoboticsAcademy/manage.py runserver 0.0.0.0:8000"
runram="python3 /manager.py 0.0.0.0 7163"

$ros_setup && echo 'ENVIRONMENT SET
'
$root && $runram
