#!/usr/bin/env python3

import os
import xacro

from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg = get_package_share_directory("ros2srrc_ur5_gazebo")

    xacro_file = os.path.join(pkg, "urdf", "ur5_robotiq_2f85.urdf.xacro")

    doc = xacro.parse(open(xacro_file))
    xacro.process_doc(doc, mappings={
        "EE": "true",
        "EE_name": "robotiq_2f85"
    })

    robot_description = {
        "robot_description": doc.toxml()
    }

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    spawn_entity = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=["-topic", "robot_description", "-entity", "ur5"],
        output="screen",
    )

    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "-c", "/controller_manager"],
    )

    joint_trajectory_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_trajectory_controller", "-c", "/controller_manager"],
    )

    gripper_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gripper_controller", "-c", "/controller_manager"],
    )

    return LaunchDescription([
        robot_state_publisher,
        spawn_entity,
        joint_state_broadcaster,
        joint_trajectory_controller,
        gripper_controller,
    ])