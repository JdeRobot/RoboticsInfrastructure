"""
Pick Place Harmonic - Main World Launcher
Wraps the spawn_robot_warehouse.launch.py from ur5_gripper_description package
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    AppendEnvironmentVariable,
)


def generate_launch_description():
    package_dir = get_package_share_directory("custom_robots")
    package_dir2 = get_package_share_directory("robotiq_description")

    ros_gz_sim = get_package_share_directory("ros_gz_sim")

    gazebo_models_path = os.path.join(package_dir, "models")
    gazebo_models2_path = os.path.join(package_dir2, "models")

    world_file_name = "warehouse_arm_harmonic.world"
    world_path = os.path.join(package_dir2, "world", world_file_name)

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
        SetEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH", gazebo_models_path + ":" + gazebo_models2_path
        )
    )

    set_env_vars_resources = AppendEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH", gazebo_models_path + ":" + gazebo_models2_path
    )

    ld.add_action(set_env_vars_resources)
    ld.add_action(gazebo_server)
    ld.add_action(world_entity_cmd)

    return ld
