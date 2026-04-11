#!/usr/bin/env python3

"""
Pick Place Harmonic - FULL (Classic-like MoveIt integration)
"""

import os
import xacro
import yaml

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def load_file(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_path = os.path.join(package_path, file_path)
    with open(absolute_path, 'r') as f:
        return f.read()


def load_yaml(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_path = os.path.join(package_path, file_path)
    with open(absolute_path, 'r') as f:
        return yaml.safe_load(f)


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


    xacro_file = os.path.join(
        get_package_share_directory("ros2srrc_ur5_gazebo"),
        "urdf",
        "ur5_robotiq_2f85.urdf.xacro"
    )

    doc = xacro.parse(open(xacro_file))
    xacro.process_doc(doc, mappings={
        "EE": "true",
        "EE_name": "robotiq_2f85"
    })

    robot_description = {
        "robot_description": doc.toxml()
    }

    robot_description_semantic = {
        "robot_description_semantic": load_file(
            "ros2srrc_ur5_moveit2",
            "config/ur5robotiq_2f85.srdf"
        )
    }

    kinematics_yaml = {
        "robot_description_kinematics": load_yaml(
            "ros2srrc_robots",
            "ur5/config/kinematics.yaml"
        )
    }

    joint_limits = {
        "robot_description_planning": load_yaml(
            "ros2srrc_robots",
            "ur5/config/joint_limits.yaml"
        )
    }

    moveit_controllers = {
        "moveit_simple_controller_manager": load_yaml(
            "ros2srrc_robots",
            "ur5/config/controller_moveit2.yaml"
        ),
        "moveit_controller_manager": "moveit_simple_controller_manager/MoveItSimpleControllerManager",
    }

    trajectory_execution = {
        "moveit_manage_controllers": True,
        "trajectory_execution.allowed_execution_duration_scaling": 1.2,
        "trajectory_execution.allowed_goal_duration_margin": 0.5,
        "trajectory_execution.allowed_start_tolerance": 0.01,
    }

    planning_scene_monitor_parameters = {
        "publish_planning_scene": True,
        "publish_geometry_updates": True,
        "publish_state_updates": True,
        "publish_transforms_updates": True,
    }


    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            joint_limits,
            moveit_controllers,
            trajectory_execution,
            planning_scene_monitor_parameters,
            {"use_sim_time": True},
        ],
    )


    robmove_node = Node(
        package="ros2srrc_execution",
        executable="robmove",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            {"use_sim_time": True},
            {"ROB_PARAM": "ur5"},
        ],
    )

    robpose_node = Node(
        package="ros2srrc_execution",
        executable="robpose",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            {"use_sim_time": True},
            {"ROB_PARAM": "ur5"},
        ],
    )

    move_node = Node(
        package="ros2srrc_execution",
        executable="move",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            {"use_sim_time": True},
            {"ROB_PARAM": "ur5"},
            {"EE_PARAM": "robotiq_2f85"},
            {"ENV_PARAM": "gazebo"},
        ],
    )

    return LaunchDescription([
        world_launch,
        robot_launch,

        TimerAction(
            period=3.0,
            actions=[move_group_node]
        ),

        TimerAction(
            period=10.0,
            actions=[robmove_node, robpose_node, move_node]
        )
    ])