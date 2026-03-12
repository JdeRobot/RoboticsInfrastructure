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

    package_dir = get_package_share_directory("custom_robots")
    robotiq_description_pkg = get_package_share_directory("robotiq_description")
    ur5_gripper_pkg = get_package_share_directory("ur5_gripper_description")
    robotiq_pkg_share_dir = get_package_share_directory("robotiq_description")

    world_path = os.path.join(
        robotiq_pkg_share_dir,
        "world",
        "warehouse_arm_harmonic.world"
    )

    gazebo_models_path = os.path.join(package_dir, "models")

    ld = LaunchDescription()

    # Plugin path (important for gz_link_attacher)
    ld.add_action(
        AppendEnvironmentVariable(
            "GZ_SIM_SYSTEM_PLUGIN_PATH",
            "/home/ws/install/gz_link_attacher/lib"
        )
    )

    # Resource paths
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

    # Launch Gazebo
    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-s", "-r", "-v", "4", world_path],
        output="screen",
    )

    # Spawn world entity
    world_entity_cmd = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-name", "world", "-file", world_path],
        output="screen",
    )

    ld.add_action(gazebo)
    ld.add_action(world_entity_cmd)

    return ld