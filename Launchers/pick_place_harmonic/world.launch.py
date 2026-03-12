"""
Pick Place Harmonic - World Launcher
Configures Gazebo resource paths
"""

import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable, AppendEnvironmentVariable
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node


def generate_launch_description():

    # ROS packages
    custom_robots_pkg = get_package_share_directory("custom_robots")
    robotiq_description_pkg = get_package_share_directory("robotiq_description")
    ur5_gripper_pkg = get_package_share_directory("ur5_gripper_description")

    # World file
    world_path = os.path.join(
        robotiq_description_pkg,
        "world",
        "warehouse_arm_harmonic.world"
    )

    # Model paths
    custom_models = os.path.join(custom_robots_pkg, "models")
    robotiq_models = os.path.join(robotiq_description_pkg, "world", "models")

    ld = LaunchDescription()

    ################################################
    # Plugin path (for gz_link_attacher)
    ################################################

    ld.add_action(
        AppendEnvironmentVariable(
            "GZ_SIM_SYSTEM_PLUGIN_PATH",
            "/home/ws/install/gz_link_attacher/lib"
        )
    )

    ################################################
    # Resource paths (models)
    ################################################

    ld.add_action(
        SetEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH",
            custom_models
        )
    )

    ld.add_action(
        AppendEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH",
            robotiq_models
        )
    )

    ################################################
    # Launch Gazebo
    ################################################

    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-s", "-r", "-v", "4", world_path],
        output="screen",
    )

    ################################################
    # Spawn world
    ################################################

    world_entity_cmd = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-name", "world", "-file", world_path],
        output="screen",
    )

    ld.add_action(gazebo)
    ld.add_action(world_entity_cmd)

    return ld