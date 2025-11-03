import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    bridge_params = os.path.join(
        get_package_share_directory("custom_robots"),
        "params",
        "f1_renault_laser_no_cam.yaml",
    )

    start_gazebo_ros_bridge_cmd = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "--ros-args",
            "-p",
            f"config_file:={bridge_params}",
        ],
        output="screen",
    )

    ld = LaunchDescription()

    # Declare the launch options
    ld.add_action(start_gazebo_ros_bridge_cmd)

    return ld
