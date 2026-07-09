import os
import re
import tempfile

import xacro

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch_ros.actions import Node


def _render_bridge(package_dir, namespace):
    """Render a per-namespace copy of the bridge yaml.

    The stock f1_renault.yaml uses fixed gz topics (F1ROS/odom, /F1ROS/cmd_vel,
    f1/laser/scan, /cam_f1_left/...). For N cars each model namespaces its plugin
    topics under its entity name, so the bridge must point at /<namespace>/...
    too. Copy the yaml and prefix every topic name with the namespace.
    """
    src = os.path.join(package_dir, "params", "f1_renault.yaml")
    with open(src) as f:
        text = f.read()

    def _prefix(match):
        key, quote, topic = match.group(1), match.group(2), match.group(3)
        return f"{key}: {quote}/{namespace}/{topic.lstrip('/')}{quote}"

    text = re.sub(
        r'(ros_topic_name|gz_topic_name):\s*(["\'])(.*?)\2',
        _prefix,
        text,
    )

    out = os.path.join(tempfile.gettempdir(), f"f1_bridge_{namespace}.yaml")
    with open(out, "w") as f:
        f.write(text)
    return out


def launch_setup(context):
    x = LaunchConfiguration("x")
    y = LaunchConfiguration("y")
    z = LaunchConfiguration("z")
    R = LaunchConfiguration("R")
    P = LaunchConfiguration("P")
    Y = LaunchConfiguration("Y")
    sensor = LaunchConfiguration("sensor").perform(context)
    mode = LaunchConfiguration("mode").perform(context)
    # entity name from RAM, used as the ROS/gz namespace so N cars don't
    # collide. defaults to "f1" so a single-car launch behaves as before.
    namespace = LaunchConfiguration("entity").perform(context) or "f1"

    package_dir = get_package_share_directory("custom_robots")
    nodes_to_start = []

    f1_sensor = "laser" if sensor == "laser" else "camera"
    f1_model = "ackermann" if mode == "ackermann" else "holonomic"

    bridge_yaml = _render_bridge(package_dir, namespace)

    # robot description (URDF) with plugin topics namespaced under the entity
    xacro_file = os.path.join(package_dir, "models", "f1", "f1.urdf.xacro")
    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "holonomic": "true" if f1_model == "holonomic" else "false",
            "ackermann": "true" if f1_model == "ackermann" else "false",
            "camera": "true" if f1_sensor == "camera" else "false",
            "laser": "true" if f1_sensor == "laser" else "false",
            "namespace": namespace,
        },
    ).toxml()
    robot_description = {"robot_description": robot_description_content}

    # all nodes run inside the entity's namespace so two cars never share node
    # names or topics (robot_state_publisher, /robot_description, the bridges).
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        namespace=namespace,
        output="screen",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic", f"/{namespace}/robot_description",
            "-name", namespace,
            "-allow_renaming", "true",
            "-x", x, "-y", y, "-z", z, "-R", R, "-P", P, "-Y", Y,
        ],
        output="screen",
    )

    gz_ros2_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        namespace=namespace,
        arguments=["--ros-args", "-p", f"config_file:={bridge_yaml}"],
        output="screen",
    )

    nodes_to_start += [robot_state_publisher_node, gz_spawn_entity, gz_ros2_bridge]

    if f1_sensor == "camera":
        gz_ros2_image_bridge = Node(
            package="ros_gz_image",
            executable="image_bridge",
            namespace=namespace,
            arguments=[f"/{namespace}/cam_f1_left/image_raw"],
            output="screen",
        )
        nodes_to_start.append(gz_ros2_image_bridge)

    return nodes_to_start


def generate_launch_description():
    declared_arguments = [
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument("x", default_value="0"),
        DeclareLaunchArgument("y", default_value="0"),
        DeclareLaunchArgument("z", default_value="0"),
        DeclareLaunchArgument("R", default_value="0"),
        DeclareLaunchArgument("P", default_value="0"),
        DeclareLaunchArgument("Y", default_value="0"),
        DeclareLaunchArgument("sensor", default_value="camera"),
        DeclareLaunchArgument("mode", default_value="holo"),
        # entity/namespace for this car; RAM passes the unique entity (e.g. f1_0)
        DeclareLaunchArgument("entity", default_value="f1"),
    ]
    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
