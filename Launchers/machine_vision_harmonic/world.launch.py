"""
Machine Vision Harmonic - World Launcher
"""

import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable


def generate_launch_description():

    world_path = "/opt/jderobot/Worlds/machine_vision_harmonic.world"

    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-r", "-v", "4", world_path],
        output="screen",
    )

    ld = LaunchDescription()

    SetEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH",
        os.path.join(
            os.environ.get("GZ_SIM_RESOURCE_PATH", ""),
            "/opt/ros/humble/share",
            "/usr/share/gz",
        )
    )

    ld.add_action(gazebo)

    return ld