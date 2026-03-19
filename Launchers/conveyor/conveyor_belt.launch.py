from launch import LaunchDescription
from launch.actions import ExecuteProcess
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():

    custom_pkg = get_package_share_directory("custom_robots")

    models_path = os.path.join(custom_pkg, "models")

    world_path = "/opt/jderobot/Worlds/conveyor_world.world"

    resource_path = models_path + ":/opt/jderobot/Worlds"

    gz_env = {
        "GZ_SIM_RESOURCE_PATH": models_path + ":/opt/jderobot/Worlds",
        "GZ_SIM_SYSTEM_PLUGIN_PATH": "/opt/ros/humble/lib",
        "LD_LIBRARY_PATH": "/opt/ros/humble/lib:/usr/lib/x86_64-linux-gnu",
        "DISPLAY": ":2",
    }

    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-s", "-r", "-v", "4", world_path],
        output="screen",
        additional_env=gz_env,
        shell=False,
    )

    return LaunchDescription([gazebo])