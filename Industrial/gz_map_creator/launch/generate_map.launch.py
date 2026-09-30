#!/usr/bin/env python3
"""
Launch file to generate and save a 2D occupancy map from a Gazebo world.

This launch file:
1. Starts Gazebo (optionally headless) with the specified world file
2. Waits for the occupancy map plugin to generate the map
3. Saves the map to YAML and PGM files using map_saver
4. Shuts down after saving

Usage:
  ros2 launch gazebo_ros_2dmap_plugin generate_map.launch.py world:=<path_to_world> map_name:=<output_name>
  
Arguments:
  world: Path to the Gazebo world file (required)
  map_name: Name for output map files (default: 'map')
  output_dir: Directory to save map files (default: current directory)
  headless: Run Gazebo without GUI (default: true)
  map_topic: Topic name for the occupancy map (default: '/map2d')
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, RegisterEventHandler, TimerAction, Shutdown
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit, OnProcessStart
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    # Declare launch arguments
    world_arg = DeclareLaunchArgument(
        'world',
        description='Path to the Gazebo world file'
    )
    
    map_name_arg = DeclareLaunchArgument(
        'map_name',
        default_value='map',
        description='Name for the output map files (without extension)'
    )
    
    output_dir_arg = DeclareLaunchArgument(
        'output_dir',
        default_value='.',
        description='Directory to save the map files'
    )
    
    headless_arg = DeclareLaunchArgument(
        'headless',
        default_value='true',
        description='Run Gazebo without GUI (headless mode)'
    )
    
    map_topic_arg = DeclareLaunchArgument(
        'map_topic',
        default_value='/map2d',
        description='Topic name for the occupancy map'
    )
    
    timeout_arg = DeclareLaunchArgument(
        'timeout',
        default_value='15.0',
        description='Time to wait for map generation (seconds)'
    )
    
    # Get launch configuration
    world = LaunchConfiguration('world')
    map_name = LaunchConfiguration('map_name')
    output_dir = LaunchConfiguration('output_dir')
    headless = LaunchConfiguration('headless')
    map_topic = LaunchConfiguration('map_topic')
    timeout = LaunchConfiguration('timeout')
    
    # Start Gazebo with the world file
    # Use gzserver (headless) or gazebo (with GUI) based on headless parameter
    gazebo_cmd = ExecuteProcess(
        condition=IfCondition(headless),
        cmd=['gzserver', world, '--verbose'],
        output='screen',
        name='gazebo_server'
    )
    
    gazebo_gui_cmd = ExecuteProcess(
        condition=IfCondition(LaunchConfiguration('headless').perform(None) == 'false'),
        cmd=['gazebo', world, '--verbose'],
        output='screen',
        name='gazebo'
    )
    
    # Wait for map generation and then save the map
    # The map_saver will be triggered after a delay to allow the plugin to generate the map
    map_saver_cmd = TimerAction(
        period=timeout,
        actions=[
            ExecuteProcess(
                cmd=[
                    'ros2', 'run', 'nav2_map_server', 'map_saver_cli',
                    '-f', [output_dir, '/', map_name],
                    '--ros-args', 
                    '-r', ['map:=', map_topic],
                    '--log-level', 'info'
                ],
                output='screen',
                name='map_saver',
                on_exit=Shutdown()
            )
        ]
    )
    
    return LaunchDescription([
        # Declare arguments
        world_arg,
        map_name_arg,
        output_dir_arg,
        headless_arg,
        map_topic_arg,
        timeout_arg,
        
        # Launch Gazebo
        gazebo_cmd,
        # gazebo_gui_cmd,  # Uncomment if you want GUI support
        
        # Save map after timeout
        map_saver_cmd,
    ])