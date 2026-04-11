#!/usr/bin/env python3

"""
Pick Place Harmonic - CLASSIC MODE (NO MoveIt)
"""

import os
import yaml
import subprocess

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

    # =========================
    # WORLD + ROBOT
    # =========================

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

    # =========================
    # XACRO → URDF
    # =========================

    xacro_file = "/home/ws/src/Industrial/ros2_SimRealRobotControl_gz/packages/ur5/ros2srrc_ur5_gazebo/urdf/ur5_robotiq_2f85.urdf.xacro"

    robot_description_content = subprocess.check_output(
        ["xacro", xacro_file],
        stderr=subprocess.STDOUT
    ).decode("utf-8")

    robot_description = {
        "robot_description": robot_description_content
    }

    # =========================
    # CONFIG (necesario para execution)
    # =========================

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

    # =========================
    # EXECUTION NODES (CLAVE)
    # =========================

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

    # =========================
    # LAUNCH
    # =========================

    return LaunchDescription([
        world_launch,
        robot_launch,

        # Espera corta para que Gazebo arranque
        TimerAction(
            period=2.0,
            actions=[robmove_node, robpose_node, move_node]
        )
    ])