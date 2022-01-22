#!/bin/sh

ros2 run xacro xacro urdf/turtlebot2.urdf.xacro > urdf/turtlebot2.urdf
ros2 launch turtlebot2 spawn_model.launch.py
