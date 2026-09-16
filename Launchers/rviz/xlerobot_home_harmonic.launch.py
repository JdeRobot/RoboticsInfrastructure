"""
XLeRobot Home - RViz + MoveIt Launcher
Launches ONLY RViz with motion planning, assumes Gazebo and the robot
(including move_group, already started by xlerobot.launch.py) are running
"""

import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import TimerAction
from ament_index_python.packages import get_package_share_directory
import xacro

NAMESPACE = "logistic_robot"


def generate_launch_description():
    pkg_share_dir = get_package_share_directory("custom_robots")
    moveit_pkg_share = get_package_share_directory("xlerobot_moveit_config")

    xacro_file = os.path.join(pkg_share_dir, "models", "xlerobot", "xlerobot.urdf.xacro")
    controllers_file = os.path.join(
        moveit_pkg_share, "config", "controller_manager.yaml"
    )

    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "namespace": NAMESPACE,
            "simulation_controllers": controllers_file,
        },
    ).toxml()

    robot_description = {"robot_description": robot_description_content}

    srdf_file = os.path.join(moveit_pkg_share, "srdf", "xlerobot.srdf")
    with open(srdf_file, "r") as f:
        robot_description_semantic = {"robot_description_semantic": f.read()}

    kinematics_yaml = os.path.join(moveit_pkg_share, "config", "kinematics.yaml")
    ompl_planning_yaml = os.path.join(moveit_pkg_share, "config", "ompl_planning.yaml")

    rviz_config_file = os.path.join(moveit_pkg_share, "rviz", "moveit.rviz")

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        namespace=NAMESPACE,
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

    # gives the robot's own launch file (move_group, controllers) a head
    # start so RViz has something real to connect to
    delay_rviz = TimerAction(
        period=5.0,
        actions=[rviz_node],
    )

    return LaunchDescription(
        [
            delay_rviz,
        ]
    )
