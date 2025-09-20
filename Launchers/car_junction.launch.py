"""
car_junction.launch.py

Entry point for the Car Junction exercise.
"""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    AppendEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    package_dir = get_package_share_directory("custom_robots")
    ros_gz_sim = get_package_share_directory("ros_gz_sim")
    use_sim_time = LaunchConfiguration("use_sim_time", default="true")
    gazebo_models_path = os.path.join(package_dir, "models")
    world_file_name = "road_junction.world"
    worlds_dir = "/opt/jderobot/Worlds"
    world_path = os.path.join(worlds_dir, world_file_name)

    gazebo_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": ["-r -s -v4 ", world_path],
            "on_exit_shutdown": "true",
        }.items(),
    )

    declare_use_simulator_cmd = DeclareLaunchArgument(
        name="use_simulator",
        default_value="True",
        description="Whether to start the simulator",
    )
    world_entity_cmd = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-name", "world", "-file", world_path],
        output="screen",
    )

    start_ros_gazebo_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock",
            "/cmd_vel", 
            "/odom",
            "/waymo/lidar/points",
        ],
        parameters=[{'use_sim_time': True}],
        output="screen",
    )
    

    start_ros_gazebo_image_bridge = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["/waymo/camera_front"],
        output="screen",
    )

    # Create the launch description and populate
    ld = LaunchDescription()
    ld.add_action(SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", gazebo_models_path))
    set_env_vars_resources = AppendEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH", os.path.join(package_dir, "models")
    )
    ld.add_action(set_env_vars_resources)
    ld.add_action(gazebo_server)
    ld.add_action(world_entity_cmd)
    ld.add_action(start_ros_gazebo_bridge)
    ld.add_action(start_ros_gazebo_image_bridge)

    return ld
