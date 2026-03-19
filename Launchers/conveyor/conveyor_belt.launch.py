from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable
import os

def generate_launch_description():

    world_path = "/opt/jderobot/Worlds/conveyor_world.world"

    gz_env = {
        "GZ_SIM_RESOURCE_PATH": "/opt/jderobot/CustomRobots/models:/opt/jderobot/Worlds",
        "GZ_SIM_SYSTEM_PLUGIN_PATH": "/opt/ros/humble/lib",
        "DISPLAY": ":2",
    }

    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-s", "-r", "-v", "4", world_path],
        output="screen",
        additional_env=gz_env,
    )

    return LaunchDescription([
        SetEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH",
            "/opt/jderobot/CustomRobots/models:/opt/jderobot/Worlds"
        ),
        gazebo
    ])