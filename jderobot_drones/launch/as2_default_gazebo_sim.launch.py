"""
as2_default_gazebo_sim.launch.py
"""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """
    Launch aerostack2 nodes
    """

    as2_sim_config = os.path.join(
        get_package_share_directory("jderobot_drones"),
        "sim_config/gzsim/as2_config.yaml",
    )

    platform_gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory("as2_platform_gazebo"), "launch"
                ),
                "/platform_gazebo_launch.py",
            ]
        ),
        launch_arguments={
            "namespace": LaunchConfiguration("namespace"),
            "platform_config_file": as2_sim_config,
            "create_bridges": "false",
        }.items(),
    )
    state_estimator = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory("as2_state_estimator"), "launch"
                ),
                "/ground_truth-state_estimator.launch.py",
            ]
        ),
        launch_arguments={
            "namespace": LaunchConfiguration("namespace"),
            "config_file": as2_sim_config,
        }.items(),
    )
    motion_controller = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory("as2_motion_controller"), "launch"
                ),
                "/pid_speed_controller-motion_controller.launch.py",
            ]
        ),
        launch_arguments={
            "namespace": LaunchConfiguration("namespace"),
            "config_file": as2_sim_config,
        }.items(),
    )
    behaviors = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory("as2_behaviors_motion"), "launch"
                ),
                "/motion_behaviors_launch.py",
            ]
        ),
        launch_arguments={
            "namespace": LaunchConfiguration("namespace"),
            "config_file": as2_sim_config,
        }.items(),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "namespace", default_value="drone0", description="Drone namespace."
            ),
            platform_gazebo,
            state_estimator,
            motion_controller,
            # behaviors,
        ]
    )
