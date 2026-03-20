import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable
from launch_ros.actions import Node


def generate_launch_description():

    world_path = "/opt/jderobot/Worlds/conveyor_world.world"

    resource_path = "/home/ws/src/CustomRobots:/opt/jderobot/Worlds"
    gz_lib_path = "/home/ws/install"

    gz_env = {
        "DISPLAY": ":2",
        "GZ_SIM_RESOURCE_PATH": resource_path,
        "GZ_SIM_SYSTEM_PLUGIN_PATH": gz_lib_path + ":/opt/ros/humble/lib",
        "LD_LIBRARY_PATH": gz_lib_path + ":/opt/ros/humble/lib:/usr/lib/x86_64-linux-gnu",
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
        SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", resource_path),
        SetEnvironmentVariable("GZ_SIM_SYSTEM_PLUGIN_PATH", gz_lib_path + ":/opt/ros/humble/lib"),
        SetEnvironmentVariable("LD_LIBRARY_PATH", gz_lib_path + ":/opt/ros/humble/lib:/usr/lib/x86_64-linux-gnu"),
        gazebo,
        world_entity_cmd,
    ])