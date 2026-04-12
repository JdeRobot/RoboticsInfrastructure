#!/usr/bin/env python3

import os
import xacro

from launch import LaunchDescription
from launch.actions import TimerAction, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_share_dir = get_package_share_directory("ros2srrc_ur5_gazebo")

    xacro_file = os.path.join(
        pkg_share_dir,
        "urdf",
        "ur5_robotiq_2f85.urdf.xacro"
    )

    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "EE": "true",
            "EE_name": "robotiq_2f85",
            "hmi": "false",
        },
    ).toxml()

    robot_description = {"robot_description": robot_description_content}

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic", "robot_description",
            "-name", "ur5",
            "-x", "0.0",
            "-y", "0.0",
            "-z", "0.9",
        ],
        output="screen",
    )

    static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0", "0", "0.9", "0", "0", "0", "world", "base_link"],
        parameters=[{"use_sim_time": True}],
    )

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
    )

    return LaunchDescription([
        robot_state_publisher,
        static_tf,
        bridge,
        TimerAction(period=3.0, actions=[spawn_entity]),
    ])