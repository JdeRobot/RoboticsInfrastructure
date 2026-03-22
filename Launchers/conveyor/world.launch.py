import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable


def generate_launch_description():

    world_path = "/opt/jderobot/Worlds/conveyor_world.world"

    return LaunchDescription([

        SetEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH",
            "/home/ws/src/CustomRobots"
        ),

        SetEnvironmentVariable(
            "GZ_SIM_SYSTEM_PLUGIN_PATH",
            "/home/ws/install:/opt/ros/humble/lib"
        ),

        SetEnvironmentVariable(
            "LD_LIBRARY_PATH",
            "/home/ws/install:/opt/ros/humble/lib:/usr/lib/x86_64-linux-gnu"
        ),

        SetEnvironmentVariable(
            "DISPLAY",
            ":2"
        ),

        ExecuteProcess(
            cmd=["gz", "sim", "-r", "-v", "4", world_path],
            output="screen",
        ),
    ])