"""
Machine Vision Harmonic - Robot Launcher
(USA EL MISMO QUE PICK&PLACE)
"""

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    ur5_gripper_pkg = get_package_share_directory("ur5_gripper_description")

    warehouse_launch_file = os.path.join(
        ur5_gripper_pkg, "launch", "spawn_robot_warehouse.launch.py"
    )

    warehouse_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(warehouse_launch_file),
        launch_arguments={
            "launch_rviz": "false",
        }.items(),
    )

    return LaunchDescription([warehouse_launch])