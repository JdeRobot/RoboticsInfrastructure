"""
Pick Place Harmonic - RViz + MoveIt Launcher
Launches ONLY: MoveIt move_group + RViz with motion planning
Assumes Gazebo and robot are already running
"""

import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import TimerAction
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # Get package directories
    moveit_config_package = "ur5_gripper_moveit_config"
    moveit_pkg_share = get_package_share_directory(moveit_config_package)

    # RViz with MoveIt configuration
    rviz_config_file = os.path.join(moveit_pkg_share, "rviz", "moveit.rviz")

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        parameters=[
            {"use_sim_time": True},
        ],
    )


    # Delay RViz after MoveIt
    delay_rviz = TimerAction(
        period=3.0,
        actions=[rviz_node],
    )

    return LaunchDescription(
        [
            delay_rviz,
        ]
    )