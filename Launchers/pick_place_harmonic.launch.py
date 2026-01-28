#!/usr/bin/env python3
"""
Pick Place Harmonic - Gazebo World Launcher
Launches ONLY: Gazebo Harmonic + UR5 Robot + Controllers
MoveIt and RViz are launched separately by the Academy
"""

import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import xacro


def generate_launch_description():
    # Get package directories
    pkg_share_dir = get_package_share_directory("ur5_gripper_description")
    robotiq_pkg_share_dir = get_package_share_directory("robotiq_description")
    
<<<<<<< HEAD
    # Workspace for gz_ros2_control
    workspace_dir = "/home/dev_ws"
    gz_lib_path = os.path.join(workspace_dir, 'install', 'gz_ros2_control', 'lib')
=======
    
    # Use native gz_ros2_control installation from ROS 2 Humble
    gz_lib_path = "/opt/ros/humble/lib"
>>>>>>> d271cd3ff6ab16b3989f49c66dc5c64a77771b10
    
    # Set environment variables for Gazebo Harmonic
    gz_env = {
        'GZ_SIM_SYSTEM_PLUGIN_PATH': f"{gz_lib_path}:{os.environ.get('GZ_SIM_SYSTEM_PLUGIN_PATH', '')}",
        'GZ_SIM_RESOURCE_PATH': f"{pkg_share_dir}/share:{robotiq_pkg_share_dir}/share:{os.environ.get('GZ_SIM_RESOURCE_PATH', '')}",
        'LD_LIBRARY_PATH': f"{gz_lib_path}:{os.environ.get('LD_LIBRARY_PATH', '')}"
    }
    
    # Process URDF with xacro
    xacro_file = os.path.join(pkg_share_dir, "urdf", "ur5_robotiq85_gripper.urdf.xacro")
    controllers_file = os.path.join(pkg_share_dir, "config", "ur5_controllers.yaml")
    
    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "ur_type": "ur5",
            "name": "ur",
            "prefix": "",
            "use_fake_hardware": "false",
            "sim_gazebo": "false",
            "sim_gz": "true",
            "simulation_controllers": controllers_file,
        }
    ).toxml()
    
    robot_description = {"robot_description": robot_description_content}
    
    # Robot state publisher
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": True}],
    )
    
    # Static transform (world → base_link)
    static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_transform_publisher",
        arguments=["0", "0", "0.9", "0", "0", "0", "world", "base_link"],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )
    
    # Gazebo Sim
    world_file = os.path.join(robotiq_pkg_share_dir, 'world', 'warehouse_arm_harmonic.world')
    gz_cmd = (
        f'export GZ_SIM_SYSTEM_PLUGIN_PATH="{gz_env["GZ_SIM_SYSTEM_PLUGIN_PATH"]}" && '
        f'export GZ_SIM_RESOURCE_PATH="{gz_env["GZ_SIM_RESOURCE_PATH"]}" && '
        f'export LD_LIBRARY_PATH="{gz_env["LD_LIBRARY_PATH"]}" && '
        f'gz sim -r -v 4 "{world_file}"'
    )
    
    gazebo = ExecuteProcess(
        cmd=['bash', '-c', gz_cmd],
        output='screen',
        shell=False
    )
    
    # Spawn robot
    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic", "robot_description",
            "-name", "ur5_robotiq",
            "-allow_renaming", "true",
            "-x", "0.0", "-y", "0.0", "-z", "0.9",
            "-R", "0.0", "-P", "0.0", "-Y", "0.0"
        ],
        output="screen",
    )
    
    # Clock bridge
    gz_ros2_bridge_clock = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )
    
    # Spawn controllers via background script (more reliable than launch system)
    controller_script = os.path.join(os.path.dirname(__file__), 'spawn_controllers.sh')
    spawn_controllers = ExecuteProcess(
        cmd=['bash', controller_script],
        output='screen',
        shell=False
    )
    
    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        spawn_entity,
        static_tf,
        gz_ros2_bridge_clock,
        spawn_controllers,  # This will run in background and spawn controllers with delays
    ])
