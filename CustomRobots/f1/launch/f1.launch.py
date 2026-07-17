import os
import xacro

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration, Command, IfElseSubstitution
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def launch_setup(context):
    use_sim_time = LaunchConfiguration("use_sim_time")
    x = LaunchConfiguration("x")
    y = LaunchConfiguration("y")
    z = LaunchConfiguration("z")
    R = LaunchConfiguration("R")
    P = LaunchConfiguration("P")
    Y = LaunchConfiguration("Y")
    gz_sensor = LaunchConfiguration("sensor")
    gz_mode = LaunchConfiguration("mode")
    gz_namespace = LaunchConfiguration("namespace")
    gz_entity = LaunchConfiguration("entity")

    package_dir = get_package_share_directory("custom_robots")

    nodes_to_start = []

    sensor = gz_sensor.perform(context)
    mode = gz_mode.perform(context)
    namespace = gz_namespace.perform(context)
    entity = gz_entity.perform(context)

    f1_sensor = "laser" if sensor == "laser" else "camera"
    f1_model = "ackermann" if mode == "ackermann" else "holonomic"

    # =========================
    # ROBOT DESCRIPTION (URDF)
    # =========================
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

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        namespace=gz_namespace,
        output="screen",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        namespace=gz_namespace,
        arguments=[
            "-topic",
            f"/{namespace}/robot_description",
            "-name",
            entity,
            "-allow_renaming",
            "true",
            "-x",
            x,
            "-y",
            y,
            "-z",
            z,
            "-R",
            R,
            "-P",
            P,
            "-Y",
            Y,
        ],
        output="screen",
    )

    gz_ros2_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        namespace=gz_namespace,
        arguments=[
            f"/{namespace}/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry",
            f"/{namespace}/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",
        ],
        output="screen",
    )

    nodes_to_start.append(robot_state_publisher_node)
    nodes_to_start.append(gz_spawn_entity)
    nodes_to_start.append(gz_ros2_bridge)

    # Sensor deppending on sensor arguments
    if f1_sensor == "camera":
        gz_ros2_image_bridge = Node(
            package="ros_gz_image",
            executable="image_bridge",
            arguments=[f"/{namespace}/camera/image_raw"],
            output="screen",
        )
        nodes_to_start.append(gz_ros2_image_bridge)
    else:
        gz_ros2_laser_bridge = Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            namespace=gz_namespace,
            arguments=[
                f"/{namespace}/laser/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
            ],
            output="screen",
        )
        nodes_to_start.append(gz_ros2_laser_bridge)

    return nodes_to_start


def generate_launch_description():
    # Add any entry parameter
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
        DeclareLaunchArgument("namespace", default_value="f1"),
        DeclareLaunchArgument("entity", default_value="f1"),
    ]

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
