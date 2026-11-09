"""
Pick Place Sorting Harmonic - RViz + MoveIt Launcher
Launches ONLY: RViz with motion planning and the overhead camera image
Assumes Gazebo and robot are already running
"""

import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import TimerAction
from ament_index_python.packages import get_package_share_directory
import xacro


def generate_launch_description():
    # Get package directories
    pkg_share_dir = get_package_share_directory("custom_robots")
    moveit_config_package = "ur5_gripper_moveit_config"
    moveit_pkg_share = get_package_share_directory(moveit_config_package)

    # Robot description (must match what's in Gazebo)
    xacro_file = os.path.join(pkg_share_dir, "models/ur5", "ur5.urdf.xacro")
    controllers_file = os.path.join(pkg_share_dir, "config", "ur5_controllers.yaml")

    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "ur_type": "ur5",
            "name": "ur",
            "prefix": "",
            "use_fake_hardware": "false",
            "sim_gazebo": "false",
            "sim_gz": "true",
            "simulation_controllers": controllers_file,
        },
    ).toxml()

    robot_description = {"robot_description": robot_description_content}

    # SRDF
    srdf_file = os.path.join(moveit_pkg_share, "srdf", "ur5_robotiq.srdf")
    with open(srdf_file, "r") as file:
        robot_description_semantic = {"robot_description_semantic": file.read()}

    # Kinematics
    kinematics_yaml = os.path.join(moveit_pkg_share, "config", "kinematics.yaml")

    # OMPL planning
    ompl_planning_yaml = os.path.join(moveit_pkg_share, "config", "ompl_planning.yaml")

    # RViz with MoveIt configuration
    rviz_config_file = os.path.join(
        "/opt/jderobot/Launchers", "rviz", "pick_place_sorting.rviz"
    )

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

    # Delay RViz until MoveIt is ready
    delay_rviz = TimerAction(
        period=3.0,
        actions=[rviz_node],
    )

    return LaunchDescription(
        [
            delay_rviz,
        ]
    )