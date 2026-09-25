"""Launch file for the MiR100 in physical mode, used with a real robot instead of the simulation.

Counterpart of mir100.launch.py for scenes of type physical, so there is no
Gazebo and nothing gets spawned. The robot's own ROS1 stack (mir_driver and
rosbridge_server) is expected to already be running outside this docker.
This file only starts robot_state_publisher and mir100_bridge, which
republishes those ROS1 topics as ROS2 under the same names mir100.launch.py
uses.

The pose arguments x, y, z, R, P, Y and entity are accepted for interface
compatibility with LauncherRobotRos2Api, which passes them to every robot
launch file, but they are not used here since there is no simulated pose to
set.
"""

import os
import xacro

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch_ros.actions import Node


def launch_setup(context):
    gz_namespace = LaunchConfiguration("namespace")
    namespace = gz_namespace.perform(context)

    package_dir = get_package_share_directory("custom_robots")
    xacro_file = os.path.join(package_dir, "models", "mir100", "mir100.urdf.xacro")
    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={"noise_level": "none", "namespace": namespace},
    ).toxml()

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        namespace=gz_namespace,
        output="screen",
        parameters=[{"robot_description": robot_description_content}, {"use_sim_time": False}],
    )

    bridge_node = Node(
        package="mir100_bridge",
        executable="bridge_node",
        namespace=gz_namespace,
        output="screen",
        parameters=[
            {
                "namespace": namespace,
                "ros1_hostname": LaunchConfiguration("ros1_hostname"),
                "ros1_port": LaunchConfiguration("ros1_port"),
            }
        ],
    )

    return [robot_state_publisher_node, bridge_node]


def generate_launch_description():
    declared_arguments = [
        DeclareLaunchArgument("use_sim_time", default_value="false"),
        DeclareLaunchArgument("x", default_value="0"),
        DeclareLaunchArgument("y", default_value="0"),
        DeclareLaunchArgument("z", default_value="0"),
        DeclareLaunchArgument("R", default_value="0"),
        DeclareLaunchArgument("P", default_value="0"),
        DeclareLaunchArgument("Y", default_value="0"),
        DeclareLaunchArgument("entity", default_value="mir100"),
        DeclareLaunchArgument("namespace", default_value="mir100"),
        DeclareLaunchArgument("ros1_hostname", default_value="localhost"),
        DeclareLaunchArgument("ros1_port", default_value="9091"),
    ]

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
