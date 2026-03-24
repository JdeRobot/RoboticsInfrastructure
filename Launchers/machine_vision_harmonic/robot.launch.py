"""
Machine Vision Harmonic - Robot Launcher
"""

import os
import xacro
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    PACKAGE_NAME = "ros2srrc_ur5"

    pkg_path = get_package_share_directory(PACKAGE_NAME + "_gazebo")

    xacro_file = os.path.join(pkg_path, "urdf", "ur5.urdf.xacro")

    doc = xacro.parse(open(xacro_file))
    xacro.process_doc(doc)

    robot_description = {"robot_description": doc.toxml()}

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0", "0", "0", "0", "0", "0", "world", "base_link"],
    )

    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name", "ur5",
            "-topic", "robot_description",
            "-x", "0",
            "-y", "0",
            "-z", "0",
            "-R", "0",
            "-P", "1.57",
            "-Y", "0",
        ],
        output="screen",
    )

    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
    )

    joint_trajectory_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_trajectory_controller"],
    )

    return LaunchDescription([
        robot_state_publisher,
        static_tf,
        spawn_entity,
        joint_state_broadcaster,
        joint_trajectory_controller,
    ])