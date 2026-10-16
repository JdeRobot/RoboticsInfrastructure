#!/bin/bash
source /opt/ros/noetic/setup.bash
source /ws/devel/setup.bash
roscore &
until rostopic list >/dev/null 2>&1; do sleep 0.5; done
roslaunch rosbridge_server rosbridge_websocket.launch port:=9091 &
exec roslaunch mir_driver mir.launch mir_hostname:=localhost disable_map:=true
