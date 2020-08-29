# Copyright 2019 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Demo for spawn_entity.

Launches Gazebo and spawns a model
"""


from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression

from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    
    # Create the launch description and populate
    ld = LaunchDescription()

    amazon_gazebo_package_dir = get_package_share_directory('amazon_robot_gazebo')
    amazon_bringup_package_dir = get_package_share_directory('amazon_robot_bringup')
    

    world = LaunchConfiguration('world')

    # Our own gazebo world from CustomRobots
    declare_world_cmd = DeclareLaunchArgument(
        'world',
        default_value=os.path.join(amazon_gazebo_package_dir, 'worlds', 'amazon_warehouse' , 'amazon_robot.model'),
        description='Full path to world model file to load')


    # Default Nav2 actions
    # Specify the actions
    start_gazebo_server_cmd = ExecuteProcess(
        cmd=['gzserver', '--verbose', '-s', 'libgazebo_ros_factory.so', '-s' , 'libgazebo_ros_force_system.so' , world],
        output='screen')

    start_gazebo_client_cmd = ExecuteProcess(
        cmd=['gzclient'], output='screen')


    spawn_robot_cmd = IncludeLaunchDescription(
                PythonLaunchDescriptionSource(os.path.join(amazon_bringup_package_dir, 'launch',
                                                           'spawn_tb3_launch.py')),
                launch_arguments={
                                  'x_pose': '5',
                                  'y_pose': '0',
                                  'z_pose': '0.1', 
                                  'robot_name': 'test'                           
                                  }.items())


    ld.add_action(spawn_robot_cmd)
    ld.add_action(declare_world_cmd)
    ld.add_action(start_gazebo_server_cmd)
    ld.add_action(start_gazebo_client_cmd)


    return ld