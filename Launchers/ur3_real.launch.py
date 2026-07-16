#!/usr/bin/env python3

import os

from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    # Mundo vacío de Gazebo
    world_path = "/usr/share/gz/gz-sim8/worlds/empty.sdf"

    # ==================================================
    # RESOURCE PATHS
    # ==================================================

    resource_path = (
        os.path.dirname(get_package_share_directory("ros2srrc_robots"))
        + ":"
        + os.path.dirname(get_package_share_directory("ros2srrc_endeffectors"))
        + ":"
        + "/home/ws/src/CustomRobots"
    )

    set_resource_path = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=resource_path,
    )

    # ==================================================
    # GAZEBO
    # ==================================================

    gz = ExecuteProcess(
        cmd=[
            "gz",
            "sim",
            "-r",
            "-s",
            "-v",
            "4",
            world_path,
        ],
        output="screen",
    )

    return LaunchDescription(
        [
            set_resource_path,
            gz,
        ]
    )