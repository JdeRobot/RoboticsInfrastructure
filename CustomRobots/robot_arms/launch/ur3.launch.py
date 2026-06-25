"""
UR3 + Robotiq - RViz Launcher
Launches ONLY RViz.
Assumes Gazebo, controllers and move_group are already running.
"""

import os
import yaml
import xacro

from launch import LaunchDescription
from launch.actions import TimerAction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def load_file(package_name, file_path):
    pkg_path = get_package_share_directory(package_name)
    with open(os.path.join(pkg_path, file_path), "r") as f:
        return f.read()


def load_yaml(package_name, file_path):
    pkg_path = get_package_share_directory(package_name)
    with open(os.path.join(pkg_path, file_path), "r") as f:
        return yaml.safe_load(f)


def generate_launch_description():

    package_dir = get_package_share_directory("custom_robots")

    # --------------------------------------------------
    # Robot Description
    # --------------------------------------------------

    xacro_file = os.path.join(
        package_dir,
        "models",
        "ur3",
        "ur3.urdf.xacro",
    )

    controllers_file = os.path.join(
        package_dir,
        "config",
        "ur3_controllers.yaml",
    )

    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "ur_type": "ur3",
            "name": "ur",
            "prefix": "",
            "use_fake_hardware": "false",
            "sim_gazebo": "false",
            "sim_gz": "true",
            "simulation_controllers": controllers_file,
            "hmi": "false",
            "EE": "true",
            "EE_name": "robotiq_2f85",
            "camera": "false",
        },
    ).toxml()

    robot_description = {
        "robot_description": robot_description_content
    }

    # --------------------------------------------------
    # Semantic Description
    # --------------------------------------------------

    robot_description_semantic = {
        "robot_description_semantic": load_file(
            "ros2srrc_ur3_moveit2",
            "config/ur3robotiq_2f85.srdf",
        )
    }

    # --------------------------------------------------
    # Kinematics
    # --------------------------------------------------

    kinematics_yaml = load_yaml(
        "ur3_gripper_moveit_config",
        "config/kinematics.yaml",
    )

    kinematics_yaml = {
        "robot_description_kinematics":
            kinematics_yaml["/**"]["ros__parameters"]
    }

    # --------------------------------------------------
    # OMPL Planning
    # --------------------------------------------------

    ompl_planning = load_yaml(
        "ur3_gripper_moveit_config",
        "config/ompl_planning.yaml",
    )

    ompl_planning = ompl_planning["/**"]["ros__parameters"]

    # --------------------------------------------------
    # RViz configuration
    # --------------------------------------------------

    rviz_config_file = os.path.join(
        get_package_share_directory("ros2srrc_ur3_moveit2"),
        "rviz",
        "moveit.rviz",
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=[
            "-d",
            rviz_config_file,
        ],
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            ompl_planning,
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