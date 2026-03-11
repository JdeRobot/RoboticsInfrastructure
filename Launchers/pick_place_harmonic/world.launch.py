"""
Pick Place Harmonic - World Launcher
Configures Gazebo resource paths
"""

import os

from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable, AppendEnvironmentVariable
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    package_dir = get_package_share_directory("custom_robots")
    robotiq_description_pkg = get_package_share_directory("robotiq_description")
    ur5_gripper_pkg = get_package_share_directory("ur5_gripper_description")
    robotiq_pkg_share_dir = get_package_share_directory("robotiq_description")

    # World path
    world_path = os.path.join(
        robotiq_pkg_share_dir,
        "world",
        "warehouse_arm_harmonic.world"
    )

    # Resource paths
    warehouse_models_path = os.path.join(
        robotiq_pkg_share_dir,
        "world",
        "models"
    )

    gazebo_models_path = os.path.join(package_dir, "models")

    ur5_share_parent = os.path.dirname(ur5_gripper_pkg)
    robotiq_share_parent = os.path.dirname(robotiq_pkg_share_dir)

    resource_path = (
        ur5_share_parent
        + ":"
        + robotiq_share_parent
        + ":"
        + warehouse_models_path
    )

    # gz_ros2_control libs
    gz_ros2_control_install = "/home/ws/install"
    gz_lib_path = os.path.join(
        gz_ros2_control_install,
        "gz_ros2_control",
        "lib"
    )

    gz_env = {
        "GZ_SIM_RESOURCE_PATH": resource_path,
        "GZ_SIM_SYSTEM_PLUGIN_PATH":
            gz_lib_path
            + ":/opt/ros/humble/lib"
            + ":/home/dev_ws/install/gz_link_attacher/lib",
        "LD_LIBRARY_PATH":
            gz_lib_path
            + ":/opt/ros/humble/lib"
            + ":/usr/lib/x86_64-linux-gnu",
        "DISPLAY": ":2",
    }

    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-r", "-v", "4", world_path],
        output="screen",
        additional_env=gz_env,
        shell=False,
    )

    ld = LaunchDescription()

    ld.add_action(
        SetEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH",
            gazebo_models_path
            + ":"
            + ur5_gripper_pkg
            + ":"
            + robotiq_description_pkg,
        )
    )

    ld.add_action(
        AppendEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH",
            gazebo_models_path
            + ":"
            + ur5_gripper_pkg
            + ":"
            + robotiq_description_pkg,
        )
    )

    ld.add_action(gazebo)

    return ld