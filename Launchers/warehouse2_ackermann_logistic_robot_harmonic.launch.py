"""
Gazebo Harmonic world launcher for warehouse2 (Ackermann robot).

Runs gz_sim with:
    RoboticsInfrastructure/Worlds/warehouse2_ackerman.world

The robot is hardcoded at the end of the world file, so it is spawned
as part of the world itself.

Extends GZ_SIM_RESOURCE_PATH with custom_robots models.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    AppendEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():

    package_dir = get_package_share_directory("custom_robots")
    ros_gz_sim = get_package_share_directory("ros_gz_sim")

    gazebo_models_path = os.path.join(package_dir, "models")

    robot_launch_dir = "/opt/jderobot/Launchers/ackermann_logistic_robot_harmonic"
    gui_config_path = (
        "/opt/jderobot/Launchers/visualization/amazon_robot_harmonic.config"
    )

    world_path = os.path.join("/opt/jderobot/Worlds", "warehouse2_ackerman.world")

    gazebo_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": [f"-r -s -v4 --gui-config {gui_config_path} {world_path}"],
            "on_exit_shutdown": "true",
        }.items(),
    )

    spawn_robot_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(robot_launch_dir, "spawn_robot.launch.py")
        )
    )

    ld = LaunchDescription()
    ld.add_action(SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", gazebo_models_path))
    ld.add_action(AppendEnvironmentVariable("GZ_SIM_RESOURCE_PATH", gazebo_models_path))
    ld.add_action(gazebo_server)
    ld.add_action(spawn_robot_cmd)
    return ld
