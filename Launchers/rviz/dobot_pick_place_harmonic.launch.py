"""
Dobot Pick Place Harmonic - RViz + MoveIt Launcher
Launches ONLY: RViz with motion planning
Assumes Gazebo and the robot are already running
"""

import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import TimerAction
from ament_index_python.packages import get_package_share_directory
import xacro


def generate_launch_description():
    pkg_share_dir = get_package_share_directory("custom_robots")
    moveit_config_package = "dobot_magician_gripper_moveit_config"
    moveit_pkg_share = get_package_share_directory(moveit_config_package)

    xacro_file = os.path.join(
        pkg_share_dir, "models/dobot_magician", "dobot_magician.urdf.xacro"
    )
    controllers_file = os.path.join(
        pkg_share_dir, "config", "dobot_magician_controllers.yaml"
    )

    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "name": "dobot_magician",
            "prefix": "",
            "use_fake_hardware": "false",
            "sim_gazebo": "false",
            "sim_gz": "true",
            "simulation_controllers": controllers_file,
        },
    ).toxml()

    robot_description = {"robot_description": robot_description_content}

    srdf_pkg_share = get_package_share_directory("ros2srrc_dobot_magician_moveit2")
    srdf_file = os.path.join(srdf_pkg_share, "config", "dobot_magician_gripper.srdf")
    with open(srdf_file, "r") as file:
        robot_description_semantic = {"robot_description_semantic": file.read()}

    kinematics_yaml = os.path.join(moveit_pkg_share, "config", "kinematics.yaml")
    ompl_planning_yaml = os.path.join(moveit_pkg_share, "config", "ompl_planning.yaml")

    rviz_config_file = os.path.join(moveit_pkg_share, "rviz", "moveit.rviz")

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        parameters=[
            robot_description,
            robot_description_semantic,
            ompl_planning_yaml,
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
