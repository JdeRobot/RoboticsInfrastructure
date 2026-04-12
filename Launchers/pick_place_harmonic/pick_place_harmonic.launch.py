#!/usr/bin/env python3

import os
import yaml

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def load_file(package_name, file_path):
    pkg_path = get_package_share_directory(package_name)
    with open(os.path.join(pkg_path, file_path), 'r') as f:
        return f.read()


def load_yaml(package_name, file_path):
    pkg_path = get_package_share_directory(package_name)
    with open(os.path.join(pkg_path, file_path), 'r') as f:
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
    # MOVEIT PARAMS
    # =========================

    robot_description_semantic = {
        "robot_description_semantic": load_file(
            "ur5_gripper_moveit_config",
            "srdf/ur5_robotiq.srdf"
        )
    }

    kinematics_yaml = {
        "robot_description_kinematics": load_yaml(
            "ur5_gripper_moveit_config",
            "config/kinematics.yaml"
        )
    }

    common_params = {}
    common_params.update(robot_description_semantic)
    common_params.update(kinematics_yaml)

    common_params.update({
        "use_sim_time": True,
        "ROB_PARAM": "ur5",
        "EE_PARAM": "robotiq_2f85",
        "ENV_PARAM": "gazebo",
    })

    # =========================
    # NODES
    # =========================

    robmove_node = Node(
        package="ros2srrc_execution",
        executable="robmove",
        output="screen",
        parameters=[common_params],
    )

    robpose_node = Node(
        package="ros2srrc_execution",
        executable="robpose",
        output="screen",
        parameters=[common_params],
    )

    move_node = Node(
        package="ros2srrc_execution",
        executable="move",
        output="screen",
        parameters=[common_params],
    )

    return LaunchDescription([
        world_launch,
        robot_launch,

        robmove_node,
        robpose_node,
        move_node
    ])