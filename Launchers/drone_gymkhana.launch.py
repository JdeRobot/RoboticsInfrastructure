"""Entry point for the Drone Gymkhana exercise."""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """Generate the launch description for drone gymkhana simulation."""
    custom_robots_share = get_package_share_directory("custom_robots")
    # same bridges file as rescue_people exercise
    bridges_path = os.path.join(custom_robots_share, "bridges", "rescue_people.yaml")
    world_path = os.path.join(
        custom_robots_share, "worlds", "drone_gymkhana_harmonic.world"
    )

    # YOU DO NOT NEED TO CHANGE ANYTHING BELOW THIS LINE #
    declare_use_simulator_cmd = DeclareLaunchArgument(
        name="use_simulator",
        default_value="True",
        description="Whether to start the simulator",
    )

    # Start Gazebo server
    gzsim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(get_package_share_directory("jderobot_drones"), "launch"),
                "/gz_sim.launch.py",
            ]
        ),
        condition=IfCondition(LaunchConfiguration("use_simulator")),
        launch_arguments={
            "namespace": "drone0",
            "bridges_file": bridges_path,
            "world_file": world_path,
        }.items(),
    )

    as2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(get_package_share_directory("jderobot_drones"), "launch"),
                "/as2_default_gazebo_sim.launch.py",
            ]
        ),
        launch_arguments={
            "namespace": "drone0",
        }.items(),
    )

    start_gazebo_frontal_image_bridge_cmd = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["/drone0/frontal_cam/image_raw"],
        output="screen",
    )

    start_gazebo_ventral_image_bridge_cmd = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["/drone0/ventral_cam/image_raw"],
        output="screen",
    )

    # Create the launch description and populate
    ld = LaunchDescription()
    ld.add_action(declare_use_simulator_cmd)
    ld.add_action(gzsim)
    ld.add_action(as2)
    ld.add_action(start_gazebo_frontal_image_bridge_cmd)
    ld.add_action(start_gazebo_ventral_image_bridge_cmd)

    return ld
