from launch import LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node

import os
import yaml
import xacro

from ament_index_python.packages import get_package_share_directory


def load_file(package_name, file_path):
    pkg_path = get_package_share_directory(package_name)
    with open(os.path.join(pkg_path, file_path), "r") as f:
        return f.read()


def load_yaml(package_name, file_path):
    pkg_path = get_package_share_directory(package_name)
    with open(os.path.join(pkg_path, file_path), "r") as f:
        return yaml.safe_load(f)


def launch_setup(context):
    ########################################################
    # OMPL
    ########################################################

    ompl_planning = load_yaml(
        "ur3_gripper_moveit_config",
        "config/ompl_planning.yaml",
    )

    ompl_planning = ompl_planning["/**"]["ros__parameters"]

    ########################################################
    # MOVE ACTION SERVER
    ########################################################

    move = Node(
        package="ros2srrc_execution",
        executable="move",
        output="screen",
        parameters=[
            ompl_planning,
            {
                "moveit_controller_manager":
                "moveit_simple_controller_manager/MoveItSimpleControllerManager"
            },
            {
                "ROB_PARAM": "ur3"
            },
            {
                "EE_PARAM": "none"
            },
            {
                "ROB_GROUP": "ur_manipulator"
            },
            {
                "use_sim_time": False
            },
        ]
    )

    ########################################################
    # ROBMOVE
    ########################################################

    robmove = Node(
        package="ros2srrc_execution",
        executable="robmove",
        output="screen",
        parameters=[
            ompl_planning,
            {
                "moveit_controller_manager":
                "moveit_simple_controller_manager/MoveItSimpleControllerManager"
            },
            {
                "ROB_PARAM": "ur3"
            },
            {
                "ROB_GROUP": "ur_manipulator"
            },
            {
                "use_sim_time": False
            },
        ]
    )

    ########################################################
    # ROBPOSE
    ########################################################

    robpose = Node(
        package="ros2srrc_execution",
        executable="robpose",
        output="screen",
        parameters=[
            ompl_planning,
            {
                "ROB_PARAM": "ur3"
            },
            {
                "ROB_GROUP": "ur_manipulator"
            },
            {
                "use_sim_time": False
            },
        ]
    )

    return [
        move,
        robmove,
        robpose,
    ]


def generate_launch_description():
    return LaunchDescription([
        OpaqueFunction(function=launch_setup)
    ])