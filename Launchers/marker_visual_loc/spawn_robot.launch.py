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

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # Get the urdf file
    model_folder = 'turtlebot3_waffle'
    urdf_path = os.path.join(
        get_package_share_directory('custom_robots'),
        'models',
        model_folder,
        'model.sdf'
    )

    # Launch configuration variables specific to simulation
    x_pose = LaunchConfiguration('x_pose', default='1.0')
    y_pose = LaunchConfiguration('y_pose', default='-1.5')
    z_pose = LaunchConfiguration('z_pose', default='7.1')

    # Declare the launch arguments
    declare_x_position_cmd = DeclareLaunchArgument(
        'x_pose', default_value='1.0',
        description='Specify namespace of the robot')

    declare_y_position_cmd = DeclareLaunchArgument(
        'y_pose', default_value='-1.5',
        description='Specify namespace of the robot')
    
    declare_z_position_cmd = DeclareLaunchArgument(
        'z_pose', default_value='7.1',
        description='Specify namespace of the robot')

    start_gazebo_ros_spawner_cmd = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', TURTLEBOT3_MODEL,
            '-file', urdf_path,
            '-x', x_pose,
            '-y', y_pose,
            '-z', z_pose
        ],
        output='screen',
    )

    bridge_params = os.path.join(
        get_package_share_directory('custom_robots'),
        'params',
        'robot_params.yaml'
    )

    start_gazebo_ros_bridge_cmd = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '--ros-args',
            '-p',
            f'config_file:={bridge_params}',
        ],
        output='screen',
    )

    start_gazebo_ros_image_bridge_cmd = Node(
        package='ros_gz_image',
        executable='image_bridge',
        arguments=['/camera/image_raw'],
        output='screen',
    )

    start_gazebo_ros_depth_bridge_cmd = Node(
        package='ros_gz_image',
        executable='image_bridge',
        arguments=['/camera/depth'],
        output='screen',
    )

    ld = LaunchDescription()

    # Declare the launch options
    ld.add_action(declare_x_position_cmd)
    ld.add_action(declare_y_position_cmd)

    # Add any conditioned actions
    ld.add_action(start_gazebo_ros_spawner_cmd)
    ld.add_action(start_gazebo_ros_bridge_cmd)
    ld.add_action(start_gazebo_ros_image_bridge_cmd)
    ld.add_action(start_gazebo_ros_depth_bridge_cmd)

    return ld