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
import xacro


def generate_launch_description():
    # Get package directories
    package_dir = get_package_share_directory("custom_robots")

    # Robot description (must match what's in Gazebo)
    xacro_file = os.path.join(
        package_dir,
        "models",
        "logistic_holonomic_robot",
        "logistic_holonomic_robot.urdf.xacro",
    )

    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "namespace": "logistic_robot",
        },
    ).toxml()

    robot_description = {"robot_description": robot_description_content}

    # RViz with MoveIt configuration
    rviz_config_file = os.path.join("/opt/jderobot/Launchers", "rviz", "warehouse1.rviz")

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        parameters=[
            robot_description,
            {"use_sim_time": True},
        ],
    )


    return LaunchDescription(
        [
            rviz_node,
        ]
    )
