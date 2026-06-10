#!/usr/bin/env python3
"""Standalone launcher for the palletizing box feeder.

Useful for testing the spawner against an already-running gz sim (the world must
already be up). The main flow wires box_spawner directly into
Launchers/palletizing.launch.py; this file is a convenience for isolated testing.

    ros2 launch custom_robots box_spawner.launch.py
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    box_spawner = Node(
        package="custom_robots",
        executable="box_spawner",
        name="box_spawner",
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    return LaunchDescription([box_spawner])
