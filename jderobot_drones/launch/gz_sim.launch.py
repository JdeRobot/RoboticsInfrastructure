"""
gz_sim.launch.py
"""

from __future__ import annotations

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, SetParameter


def generate_launch_description():
    """Entrypoint"""
    launch_description = LaunchDescription(
        [
            DeclareLaunchArgument("namespace", description="Namespace to use"),
            DeclareLaunchArgument("world_file", description="Gazebo SDF world file"),
            DeclareLaunchArgument(
                "bridges_file", description="ROS-GZ bridge YAML file"
            ),
            SetParameter(name="use_sim_time", value="true"),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [
                        os.path.join(
                            get_package_share_directory("ros_gz_sim"), "launch"
                        ),
                        "/gz_sim.launch.py",
                    ]
                ),
                launch_arguments={
                    "gz_args": ["-v 4 -s -r ", LaunchConfiguration("world_file")]
                }.items(),
            ),
            Node(
                package="ros_gz_bridge",
                executable="parameter_bridge",
                namespace=LaunchConfiguration("namespace"),
                output="screen",
                parameters=[
                    {"config_file": LaunchConfiguration("bridges_file")},
                ],
            ),
            Node(
                package="as2_gazebo_assets",
                executable="ground_truth_bridge",
                namespace=LaunchConfiguration("namespace"),
                output="screen",
                parameters=[
                    {
                        "name_space": LaunchConfiguration("namespace"),
                        "pose_frame_id": "earth",
                        "twist_frame_id": [
                            LaunchConfiguration("namespace"),
                            "/base_link",
                        ],
                    },
                ],
            ),
        ]
    )

    return launch_description
