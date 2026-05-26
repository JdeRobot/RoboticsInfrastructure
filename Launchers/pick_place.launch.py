#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    world_file_name = "warehouse_arm_harmonic.world"
    worlds_dir = "/opt/jderobot/Worlds"
    world_path = os.path.join(worlds_dir, world_file_name)

    # Paths
    gz_ros2_control_path = "/home/ws/install/gz_ros2_control/lib"
    gz_link_attacher_path = "/home/ws/install/gz_link_attacher/lib"

    gz_plugin_path = (
        gz_link_attacher_path + ":" + gz_ros2_control_path + ":" + "/opt/ros/humble/lib"
    )

    resource_path = (
        os.path.dirname(get_package_share_directory("ur5_gripper_description"))
        + ":"
        + os.path.dirname(get_package_share_directory("robotiq_description"))
        + ":"
        + os.path.join(
            get_package_share_directory("robotiq_description"), "world", "models"
        )
    )

    set_resource_path = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH", value=resource_path
    )

    set_gz_plugin_path = SetEnvironmentVariable(
        name="GZ_SIM_SYSTEM_PLUGIN_PATH", value=gz_plugin_path
    )

    existing_ld = os.environ.get("LD_LIBRARY_PATH", "")

    set_ld_library_path = SetEnvironmentVariable(
        name="LD_LIBRARY_PATH",
        value=gz_plugin_path + ":/usr/lib/x86_64-linux-gnu:" + existing_ld,
    )

    gz = ExecuteProcess(
        cmd=["gz", "sim", "-r", "-s", "-v", "4", world_path],
        output="screen",
    )

    return LaunchDescription(
        [set_gz_plugin_path, set_ld_library_path, set_resource_path, gz]
    )
