import os
import xacro

from launch import LaunchDescription
from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    xacro_file = os.path.join(
        get_package_share_directory("ros2srrc_robots"),
        "ur3",
        "urdf",
        "ur3.urdf.xacro",
    )

    robot_description = {
        "robot_description": xacro.process_file(
            xacro_file,
            mappings={
                "bringup": "false",
                "hmi": "false",
                "EE": "false",
                "EE_name": "none",
            },
        ).toxml()
    }

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[
            robot_description,
            {"use_sim_time": True},
        ],
    )

    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-topic",
            "robot_description",
            "-name",
            "ur3",
            "-x",
            "0",
            "-y",
            "0",
            "-z",
            "1.0",
        ],
    )

    return LaunchDescription([
        robot_state_publisher,
        spawn_robot,
    ])