#!/usr/bin/env python3

import os

from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable

from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node


def generate_launch_description():

    world_path = "/opt/jderobot/Scenes/sausage_exercise.world"

    # ==================================================
    # PLUGIN PATHS
    # ==================================================

    gz_ros2_control_path = "/home/ws/install/gz_ros2_control/lib"
    gz_link_attacher_path = "/home/ws/install/gz_link_attacher/lib"
    conveyor_plugin_path = "/home/ws/install/conveyor_belt_plugin/lib"

    gz_plugin_path = (
        conveyor_plugin_path
        + ":"
        + gz_link_attacher_path
        + ":"
        + gz_ros2_control_path
        + ":"
        + "/opt/ros/humble/lib"
    )

    # ==================================================
    # RESOURCE PATHS
    # ==================================================

    resource_path = (
        os.path.dirname(get_package_share_directory("ros2srrc_ur3_gazebo"))
        + ":"
        + os.path.dirname(get_package_share_directory("ros2srrc_robots"))
        + ":"
        + os.path.dirname(get_package_share_directory("ros2srrc_endeffectors"))
        + ":"
        + "/home/ws/src/CustomRobots"
    )

    set_resource_path = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=resource_path,
    )

    set_gz_plugin_path = SetEnvironmentVariable(
        name="GZ_SIM_SYSTEM_PLUGIN_PATH",
        value=gz_plugin_path,
    )

    existing_ld = os.environ.get("LD_LIBRARY_PATH", "")

    set_ld_library_path = SetEnvironmentVariable(
        name="LD_LIBRARY_PATH",
        value=gz_plugin_path + ":/usr/lib/x86_64-linux-gnu:" + existing_ld,
    )

    # ==================================================
    # GAZEBO
    # ==================================================

    gz = ExecuteProcess(
        cmd=["gz", "sim", "-r", "-s", "-v", "4", world_path],
        output="screen",
    )

    gz_ros2_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
        ],
        output="screen",
    )

    # ==================================================
    # SAUSAGE SPAWNER
    # ==================================================

    sausage_spawner = ExecuteProcess(
        cmd=["python3", "home/ws/src/CustomRobots/conveyor_belt/spawn_sausage.py"],
        output="screen",
    )

    return LaunchDescription(
        [
            set_gz_plugin_path,
            set_ld_library_path,
            set_resource_path,
            gz,
            gz_ros2_bridge,
            sausage_spawner,
        ]
    )
