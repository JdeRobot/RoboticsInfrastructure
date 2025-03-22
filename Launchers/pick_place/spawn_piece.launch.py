#!/usr/bin/env python3
#
# Copyright 2019 ROBOTIS CO., LTD.
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
#
# Authors: Darby Lim

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    piece_name = LaunchConfiguration('name', default='red_box_small')
    urdf_file_name = LaunchConfiguration('path', default='objects/red_box_small.urdf')

    x_pose = LaunchConfiguration('x', default=0)
    y_pose = LaunchConfiguration('y', default=0)
    z_pose = LaunchConfiguration('z', default=1.01)

    print('urdf_file_name : {}'.format(urdf_file_name))

    urdf_path = os.path.join(
        get_package_share_directory('custom_robots'),
        'urdf',
        urdf_file_name)

    with open(urdf_path, 'r') as infp:
        piece_desc = infp.read()

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation (Gazebo) clock if true'),

        Node(
            package='gazebo_ros',
            executable='spawn_model.py',
            output='screen',
            arguments=[
                '-model', piece_name,
                '-urdf', piece_desc,
                '-x', x_pose,
                '-y', y_pose,
                '-z', z_pose,
            ],
        )
    ])