"""
Pick Place Harmonic - World Launcher
Configures Gazebo resource paths
"""

import os
from launch import LaunchDescription
from launch.actions import SetEnvironmentVariable, AppendEnvironmentVariable
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    package_dir = get_package_share_directory("custom_robots")
    robotiq_description_pkg = get_package_share_directory("robotiq_description")
    ur5_gripper_pkg = get_package_share_directory("ur5_gripper_description")

    gazebo_models_path = os.path.join(package_dir, "models")

    ld = LaunchDescription()

    ld.add_action(
        SetEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH",
            gazebo_models_path + ":" + ur5_gripper_pkg + ":" + robotiq_description_pkg,
        )
    )

    ld.add_action(
        AppendEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH",
            gazebo_models_path + ":" + ur5_gripper_pkg + ":" + robotiq_description_pkg,
        )
    )

    return ld