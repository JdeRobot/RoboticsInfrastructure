#!/usr/bin/env python3
"""Launch the feeder against an already-running Gazebo world."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    package_dir = get_package_share_directory("custom_robots")
    task_config = os.path.join(package_dir, "config", "palletizing_task.yaml")

    box_spawner = Node(
        package="custom_robots",
        executable="box_spawner",
        name="box_spawner",
        output="screen",
        parameters=[{"use_sim_time": True}, {"task_config": task_config}],
    )

    return LaunchDescription([box_spawner])
