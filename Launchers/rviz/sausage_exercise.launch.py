"""
UR3 + Robotiq - RViz Launcher
Launches ONLY RViz with MoveIt Motion Planning
Assumes Gazebo and robot are already running
"""

import os
import xacro
import yaml

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import TimerAction

from ament_index_python.packages import get_package_share_directory

def load_yaml(package_name, file_path):
    pkg_path = get_package_share_directory(package_name)
    with open(os.path.join(pkg_path, file_path), "r") as f:
        return yaml.safe_load(f)


def generate_launch_description():

    # =====================================================
    # Packages
    # =====================================================

    moveit_pkg_share = get_package_share_directory(
        "ros2srrc_ur3_moveit2"
    )
    

    gazebo_pkg_share = get_package_share_directory(
        "ros2srrc_ur3_gazebo"
    )

    # =====================================================
    # URDF
    # =====================================================

    xacro_file = os.path.join(
        gazebo_pkg_share,
        "urdf",
        "ur3_robotiq_2f85.urdf.xacro",
    )

    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "bringup": "false",
            "hmi": "false",
            "robot_ip": "0.0.0.0",
            "EE": "true",
            "EE_name": "robotiq_2f85",
            "camera": "false",
            "script_filename": "none",
            "input_recipe_filename": "none",
            "output_recipe_filename": "none",
        },
    ).toxml()

    robot_description = {
        "robot_description": robot_description_content
    }

    # =====================================================
    # SRDF
    # =====================================================

    srdf_file = os.path.join(
        moveit_pkg_share,
        "config",
        "ur3robotiq_2f85.srdf",
    )

    with open(srdf_file, "r") as file:
        robot_description_semantic = {
            "robot_description_semantic": file.read()
        }

    # =====================================================
    # MoveIt Config Files
    # =====================================================

    kinematics_yaml = {
        "robot_description_kinematics": load_yaml(
            "ros2srrc_robots",
            "ur3/config/kinematics.yaml",
        )
    }

    ompl_planning = load_yaml(
        "ros2srrc_robots",
        "ur3/config/ompl_planning.yaml",
    )

    ompl_planning = ompl_planning["/**"]["ros__parameters"]

    # =====================================================
    # RViz Config
    # =====================================================

    rviz_config_file = (
        "/home/ws/src/Industrial/ros2_SimRealRobotControl_gz/"
        "packages/ur3/ros2srrc_ur3_moveit2/rviz/moveit.rviz"
    )

    print("MOVEIT PKG =", moveit_pkg_share)
    print("RVIZ FILE =", rviz_config_file)

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        parameters=[
            robot_description,
            robot_description_semantic,
            ompl_planning,
            kinematics_yaml,
            {"use_sim_time": True},
        ],
    )

    delay_rviz = TimerAction(
        period=3.0,
        actions=[rviz_node],
    )

    return LaunchDescription(
        [
            delay_rviz,
        ]
    )