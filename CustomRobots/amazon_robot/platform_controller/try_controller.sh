#!/bin/bash

# instructions to try platform controller:
mv /home/ws/src/CustomRobots/amazon_robot/platform_controller /home/ws/src/platform_controller
cd /home/ws && colcon build --symlink-install --packages-select platform_controller
source /home/ws/install/setup.bash 
/start_vnc_gpu.sh 0 5900 6080
sleep 3
VGL_DISPLAY=/dev/dri/card0 vglrun ros2 launch custom_robots amazon_warehouse.launch.py &
sleep 4
ros2 run platform_controller move_platform &
# ros2 topic pub --once  /send_effort std_msgs/String "data: load"