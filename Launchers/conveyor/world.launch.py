import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess


def generate_launch_description():

    world_path = "/opt/jderobot/Worlds/conveyor_world.world"

    gz_env = {
        "DISPLAY": ":2",
        "GZ_SIM_RESOURCE_PATH": "/home/ws/src/CustomRobots",
        "GZ_SIM_SYSTEM_PLUGIN_PATH": "/home/ws/install/conveyor_belt_plugin/lib:/opt/ros/humble/lib",
        "LD_LIBRARY_PATH": "/home/ws/install/conveyor_belt_plugin/lib:/opt/ros/humble/lib:/usr/lib/x86_64-linux-gnu",
    }

    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-r", "-v", "4", world_path],
        output="screen",
        additional_env=gz_env,
        shell=False,
    )

    return LaunchDescription([
        gazebo,
    ])