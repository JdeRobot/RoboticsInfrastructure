"""
Machine Vision Harmonic - World Launcher (FIXED)
"""

import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    world_path = "/opt/jderobot/Worlds/machine_vision_harmonic.world"

    ur5_pkg = get_package_share_directory("ur5_gripper_description")
    robotiq_pkg = get_package_share_directory("robotiq_description")

    resource_path = (
        os.path.dirname(ur5_pkg) + ":" +
        os.path.dirname(robotiq_pkg)
    )

    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-r", "-v", "4", world_path],
        output="screen",
        additional_env={
            "GZ_SIM_RESOURCE_PATH": resource_path
        }
    )

    return LaunchDescription([gazebo])