from launch import LaunchDescription
from launch.actions import ExecuteProcess
import os

def generate_launch_description():

    world_path = "/home/ws/Worlds/conveyor_world.world"

    gz_env = {
        "GZ_SIM_RESOURCE_PATH": "/home/ws/CustomRobots",
        "GZ_SIM_SYSTEM_PLUGIN_PATH": "/opt/ros/humble/lib",
        "DISPLAY": ":2",
    }

    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-r", world_path],
        output="screen",
        additional_env=gz_env,
    )

    return LaunchDescription([gazebo])