import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    AppendEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    package_dir = get_package_share_directory("custom_robots")
    ros_gz_sim = get_package_share_directory("ros_gz_sim")

    gazebo_models_path = os.path.join(package_dir, "models")

    world_file_name = "labyrinth_escape.world"
    worlds_dir = "/opt/jderobot/Worlds"
    world_path = os.path.join(worlds_dir, world_file_name)

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

    ld.add_action(SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", gazebo_models_path))
    set_env_vars_resources = AppendEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH", os.path.join(package_dir, "models")
    )
    ld.add_action(set_env_vars_resources)

    ld.add_action(gazebo_server)
    ld.add_action(world_entity_cmd)

    return ld
