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
    gz_noise = LaunchConfiguration("noise")
    gz_namespace = LaunchConfiguration("namespace")

    package_dir = get_package_share_directory("custom_robots")

    nodes_to_start = []

    namespace = gz_namespace.perform(context)

    # =========================
    # ROBOT DESCRIPTION (URDF)
    # =========================
    xacro_file = os.path.join(
        package_dir,
        "model",
        "dingo",
        "dingo.urdf.xacro",
    )

    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "namespace": namespace,
            "noise_level": gz_noise.perform(context),
        },
    ).toxml()

    robot_description = {"robot_description": robot_description_content}

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        namespace=gz_namespace,
        arguments=[
            "-topic",
            "/robot_description",
            "-name",
            namespace,
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
        arguments=[
            f"/{namespace}/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry",
            f"/{namespace}/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist",
            f"/{namespace}/laser/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
        ],
        output="screen",
    )

    nodes_to_start.append(robot_state_publisher_node)
    nodes_to_start.append(gz_spawn_entity)
    nodes_to_start.append(gz_ros2_bridge)

    return nodes_to_start


def generate_launch_description():
    declared_arguments = []

    # Add any entry parameter
    declared_arguments.append(
        DeclareLaunchArgument("use_sim_time", default_value="true")
    )
    declared_arguments.append(DeclareLaunchArgument("x", default_value="0"))
    declared_arguments.append(DeclareLaunchArgument("y", default_value="0"))
    declared_arguments.append(DeclareLaunchArgument("z", default_value="0"))
    declared_arguments.append(DeclareLaunchArgument("R", default_value="0"))
    declared_arguments.append(DeclareLaunchArgument("P", default_value="0"))
    declared_arguments.append(DeclareLaunchArgument("Y", default_value="0"))
    declared_arguments.append(DeclareLaunchArgument("noise", default_value="none"))
    declared_arguments.append(
        DeclareLaunchArgument(
            "namespace", description="Namespace to use", default_value="do150"
        )
    )

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
