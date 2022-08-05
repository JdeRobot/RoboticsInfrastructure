#!/usr/bin/env bash

# To run at startup, add the line below to 'Startup Applications'
# gnome-terminal -e "/path/to/this/file/startup_joystick.bash"

# Source ROS source or binary workspace
if [ -e "$HOME/dbw_ws/devel/setup.bash" ]; then
  source $HOME/dbw_ws/devel/setup.bash
else
  source `find /opt/ros -name setup.bash | sort -r | head -1`
fi

# Launch
roslaunch dbw_mkz_joystick_demo joystick_demo.launch sys:=true rviz:=false

