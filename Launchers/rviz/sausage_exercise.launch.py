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

    pkg_share_dir = get_package_share_directory("custom_robots")
    moveit_pkg_share = get_package_share_directory("ros2srrc_ur3_moveit2")

    # =====================================================
    # URDF
    # =====================================================

    xacro_file = os.path.join(
        pkg_share_dir,
        "models",
        "ur3",
        "ur3.urdf.xacro",
    )

    controllers_file = os.path.join(
        pkg_share_dir,
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

    kinematics_yaml = load_yaml(
        "ur3_gripper_moveit_config",
        "config/kinematics.yaml",
    )

    kinematics_yaml = {
        "robot_description_kinematics":
            kinematics_yaml["/**"]["ros__parameters"]
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