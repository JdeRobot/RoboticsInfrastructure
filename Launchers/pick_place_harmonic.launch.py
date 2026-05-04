"""
Pick Place Harmonic - Main World Launcher
Wraps the spawn_robot_warehouse.launch.py from ur5_gripper_description package
"""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    package_dir = get_package_share_directory("custom_robots")
    package_dir2 = get_package_share_directory("robotiq_description")

    ros_gz_sim = get_package_share_directory("ros_gz_sim")

    gazebo_models_path = os.path.join(package_dir, "models")
    gazebo_models2_path = os.path.join(package_dir2, "world", "models")

    world_file_name = "warehouse_arm_harmonic.world"
    world_path = os.path.join(package_dir2, "world", world_file_name)

    resource_path = (
        gazebo_models_path
        + ":"
        + os.path.dirname(package_dir2)
        + ":"
        + gazebo_models2_path
    )

    gazebo_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": ["-s -v4 ", world_path],
            "on_exit_shutdown": "true",
        }.items(),
    )

    world_entity_cmd = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-name", "world", "-file", world_path],
        output="screen",
    )

    ld = LaunchDescription()

    ld.add_action(
        SetEnvironmentVariable(name="GZ_SIM_RESOURCE_PATH", value=resource_path)
    )

    ld.add_action(gazebo_server)
    ld.add_action(world_entity_cmd)

    return ld
