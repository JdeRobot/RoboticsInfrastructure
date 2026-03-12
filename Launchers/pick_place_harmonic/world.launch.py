"""
Pick Place Harmonic - World Launcher
Configures Gazebo resource paths
"""

import os

from launch import LaunchDescription
from launch.actions import ExecuteProcess, AppendEnvironmentVariable
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    ################################################
    # Packages
    ################################################

    custom_robots_pkg = get_package_share_directory("custom_robots")
    robotiq_description_pkg = get_package_share_directory("robotiq_description")

    ################################################
    # World file
    ################################################

    world_path = os.path.join(
        robotiq_description_pkg,
        "world",
        "warehouse_arm_harmonic.world"
    )

    ################################################
    # Model paths
    ################################################

    custom_models = os.path.join(custom_robots_pkg, "models")
    robotiq_models = os.path.join(robotiq_description_pkg, "world", "models")

    ################################################
    # Plugin path
    ################################################

    plugin_path = "/home/ws/install/gz_link_attacher/lib"

    ld = LaunchDescription()

    ################################################
    # Add Gazebo system plugin path
    ################################################

    ld.add_action(
        AppendEnvironmentVariable(
            "GZ_SIM_SYSTEM_PLUGIN_PATH",
            plugin_path
        )
    )

    ################################################
    # Add model resource paths
    ################################################

    ld.add_action(
        AppendEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH",
            robotiq_models
        )
    )

    ld.add_action(
        AppendEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH",
            custom_models
        )
    )

    ################################################
    # Launch Gazebo
    ################################################

    gazebo = ExecuteProcess(
        cmd=[
            "gz",
            "sim",
            "-r",
            "-v", "4",
            world_path
        ],
        output="screen",
    )

    ld.add_action(gazebo)

    return ld