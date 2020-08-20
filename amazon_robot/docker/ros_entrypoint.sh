#!/bin/bash
set -e

# setup ros environment
source "/opt/ros/$ROS_DISTRO/setup.bash"
sleep 2s
source "/opt/overlay_ws/install/setup.sh"
sleep 2s
source "/opt/warehouse_ws/install/setup.sh"
exec "$@"