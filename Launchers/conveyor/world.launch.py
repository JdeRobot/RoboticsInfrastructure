import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable


def generate_launch_description():

    world_path = "/opt/jderobot/Worlds/mi_mundo.world"

    set_display = SetEnvironmentVariable("DISPLAY", ":1")

    gazebo = ExecuteProcess(
        cmd=["gz", "sim", world_path],
        output="screen"
    )

    return LaunchDescription([
        set_display,
        gazebo
    ])