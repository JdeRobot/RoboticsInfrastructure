import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable
from launch_ros.actions import Node


def generate_launch_description():

    world_path = "/opt/jderobot/Worlds/mi_mundo.world"

    gz_env = {
        "DISPLAY": ":2",
    }

    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-s", "-r", "-v", "4", world_path],
        output="screen",
        additional_env=gz_env,
        shell=False,
    )

    world_entity_cmd = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-name", "world", "-file", world_path],
        output="screen",
    )

    return LaunchDescription([
        SetEnvironmentVariable("DISPLAY", ":2"),
        gazebo,
        world_entity_cmd,
    ])