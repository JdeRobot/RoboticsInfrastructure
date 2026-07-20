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
    gz_entity = LaunchConfiguration("entity")

    package_dir = get_package_share_directory("custom_robots")

    nodes_to_start = []

    noise = gz_noise.perform(context)
    namespace = gz_namespace.perform(context)
    entity = gz_entity.perform(context)

    # =========================
    # ROBOT DESCRIPTION (URDF)
    # =========================
    xacro_file = os.path.join(
        package_dir,
        "model",
        "rover_4wd",
        "rover_4wd.urdf.xacro",
    )

    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "noise_level": noise,
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
            f"/{namespace}/laser/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
            f"/{namespace}/pose@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V",
            f"/{namespace}/imu@sensor_msgs/msg/Imu[gz.msgs.IMU",
            f"/{namespace}/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model",
        ],
        remappings=[
            (f"/{namespace}/pose", "/tf"),
        ],
        output="screen",
    )

    nodes_to_start.append(robot_state_publisher_node)
    nodes_to_start.append(gz_spawn_entity)
    nodes_to_start.append(gz_ros2_bridge)

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
        DeclareLaunchArgument("noise", default_value="none"),
        DeclareLaunchArgument("namespace", default_value="rover_4wd"),
        DeclareLaunchArgument("entity", default_value="rover_4wd"),
    ]

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
