"""
ROS - Gazebo bridge launcher for the holonomic logistic robot (Harmonic).

Starts ros_gz_bridge parameter_bridge using the
holonomic_logistic_robot_harmonic.yaml configuration file
from the custom_robots package.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    bridge_params = os.path.join(
        get_package_share_directory("custom_robots"),
        "params",
        "amazon_robot_harmonic.yaml",
    )

    bridge_cmd = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["--ros-args", "-p", f"config_file:={bridge_params}"],
        output="screen",
    )

    ld = LaunchDescription()

    ld.add_action(bridge_cmd)

    return ld
