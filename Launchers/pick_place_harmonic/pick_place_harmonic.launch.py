#!/usr/bin/env python3

"""
Pick Place Harmonic - Main Launcher (FULL)
"""

import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    base_dir = os.path.dirname(__file__)

    world_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(base_dir, "world.launch.py")
        )
    )

    robot_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(base_dir, "robot.launch.py")
        )
    )

    moveit_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("ur5_gripper_moveit_config"),
                "launch",
                "move_group.launch.py"
            )
        )
    )

    robmove_node = Node(
        package="ros2srrc_execution",
        executable="robmove",
        output="screen",
        parameters=[
            {"use_sim_time": True},
            {"ROB_PARAM": "ur5"}
        ],
    )

    robpose_node = Node(
        package="ros2srrc_execution",
        executable="robpose",
        output="screen",
        parameters=[
            {"use_sim_time": True},
            {"ROB_PARAM": "ur5"}
        ],
    )

    move_node = Node(
        package="ros2srrc_execution",
        executable="move",
        output="screen",
        parameters=[
            {"use_sim_time": True},
            {"ROB_PARAM": "ur5"},
            {"EE_PARAM": "robotiq"},
            {"ENV_PARAM": "gazebo"},
        ],
    )


    delayed_moveit = TimerAction(
        period=5.0,
        actions=[moveit_launch]
    )

    delayed_interfaces = TimerAction(
        period=8.0,
        actions=[robmove_node, robpose_node, move_node]
    )

    return LaunchDescription([
        world_launch,
        robot_launch,
        delayed_moveit,
        delayed_interfaces
    ])