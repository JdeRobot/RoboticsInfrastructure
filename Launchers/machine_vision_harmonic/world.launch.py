"""
Machine Vision Harmonic - World Launcher
"""

import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable


def generate_launch_description():

    base_dir = os.path.dirname(__file__)

    world_path = os.path.join(base_dir, "machine_vision_harmonic.world")

    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-r", "-v", "4", world_path],
        output="screen",
    )

    ld = LaunchDescription()

    ld.add_action(
        SetEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH",
            os.environ.get("GZ_SIM_RESOURCE_PATH", "")
        )
    )

    ld.add_action(gazebo)

    return ld