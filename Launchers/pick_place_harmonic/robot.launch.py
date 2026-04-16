"""
Pick Place Harmonic - Robot Launcher
Wraps spawn_robot_warehouse.launch.py
"""

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    try:
        ur5_gripper_pkg = get_package_share_directory("ur5_gripper_description")
    except Exception as e:
        print(f"ERROR: Cannot find ur5_gripper_description package: {e}")
        print("Make sure packages are built in /home/ws")
        raise

    warehouse_launch_file = os.path.join(
        ur5_gripper_pkg, "launch", "spawn_robot_warehouse.launch.py"
    )

    print(f"Including launch file: {warehouse_launch_file}")

    warehouse_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(warehouse_launch_file),
        launch_arguments={
            "launch_rviz": "false",
        }.items(),
    )

    return LaunchDescription([warehouse_launch])