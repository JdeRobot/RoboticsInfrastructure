#!/usr/bin/env python3

"""
Pick Place Harmonic - Robot Launcher
Wraps spawn_robot_warehouse.launch.py
"""

import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg = get_package_share_directory("ros2srrc_ur5_gazebo")

    launch_file = os.path.join(pkg, "launch", "ur5.launch.py")

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(launch_file),
            launch_arguments={
                "rviz": "false"
            }.items(),
        )
    ])
