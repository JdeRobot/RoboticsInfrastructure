#!/usr/bin/env python3

import os
import xacro

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import TimerAction

from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    # =====================================================
    # Packages
    # =====================================================

    pkg_share_dir = get_package_share_directory("custom_robots")

    # =====================================================
    # URDF
    # =====================================================

    xacro_file = os.path.join(
        pkg_share_dir,
        "models",
        "ur3",
        "ur3.urdf.xacro",
    )

    controllers_file = os.path.join(
        pkg_share_dir,
        "config",
        "ur3_controllers.yaml",
    )

    robot_description = {
        "robot_description": xacro.process_file(
            xacro_file,
            mappings={
                "ur_type": "ur3",
                "name": "ur",
                "prefix": "",
                "use_fake_hardware": "true",
                "sim_gazebo": "false",
                "sim_gz": "false",
                "simulation_controllers": controllers_file,
                "hmi": "false",
                "EE": "false",
                "camera": "false",
            },
        ).toxml()
    }

    # =====================================================
    # Robot State Publisher
    # =====================================================

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[
            robot_description,
            {"use_sim_time": False},
        ],
    )

    # =====================================================
    # Joint State Publisher
    # =====================================================

    joint_state_publisher = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        output="screen",
    )

    # =====================================================
    # RViz
    # =====================================================

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        output="screen",
    )

    return LaunchDescription(
        [
            robot_state_publisher,
            joint_state_publisher,
            TimerAction(
                period=1.0,
                actions=[rviz],
            ),
        ]
    )