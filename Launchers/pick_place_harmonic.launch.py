"""
Pick Place Harmonic - Main World Launcher  
Wraps the spawn_robot_warehouse.launch.py from ur5_gripper_description package
Academy launches this with launch_rviz=false
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # Get package directory
    try:
        ur5_gripper_pkg = get_package_share_directory('ur5_gripper_description')
    except Exception as e:
        print(f"ERROR: Cannot find ur5_gripper_description package: {e}")
        print("Make sure packages are built in /home/ws")
        raise
    
    # Path to spawn_robot_warehouse launch file
    warehouse_launch_file = os.path.join(
        ur5_gripper_pkg,
        'launch',
        'spawn_robot_warehouse.launch.py'
    )
    
    print(f"Including launch file: {warehouse_launch_file}")
    
    # Include the warehouse launch with launch_rviz=false (Academy launches RViz separately)
    warehouse_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(warehouse_launch_file),
        launch_arguments={
            'launch_rviz': 'false',  # Academy launches RViz separately
        }.items()
    )
    
    return LaunchDescription([
        warehouse_launch,
    ])
