import os
import xacro

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch_ros.actions import Node


def launch_setup(context):
    x = LaunchConfiguration("x")
    y = LaunchConfiguration("y")
    z = LaunchConfiguration("z")
    R = LaunchConfiguration("R")
    P = LaunchConfiguration("P")
    Y = LaunchConfiguration("Y")
    sensor = LaunchConfiguration("sensor").perform(context)
    noise = LaunchConfiguration("noise").perform(context)
    namespace = LaunchConfiguration("namespace").perform(context)
    entity = LaunchConfiguration("entity").perform(context)

    package_dir = get_package_share_directory("custom_robots")
    xacro_file = os.path.join(
        package_dir, "models", "turtlebot3", "turtlebot3_burger.urdf.xacro"
    )

    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "camera": "true" if sensor == "camera" else "false",
            "noise_level": noise,
            "namespace": namespace,
        },
    ).toxml()

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        namespace=namespace,
        output="screen",
        parameters=[
            {"robot_description": robot_description_content, "use_sim_time": True}
        ],
    )

    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        namespace=namespace,
        arguments=[
            "-topic", f"/{namespace}/robot_description",
            "-name", entity,
            "-allow_renaming", "true",
            "-x", x, "-y", y, "-z", z,
            "-R", R, "-P", P, "-Y", Y,
        ],
        output="screen",
    )

    # The LDS and the IMU are always on, like on the real robot
    gz_ros2_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        namespace=namespace,
        arguments=[
            f"/{namespace}/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry",
            f"/{namespace}/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist",
            f"/{namespace}/laser/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
            f"/{namespace}/imu@sensor_msgs/msg/Imu[gz.msgs.IMU",
        ],
        output="screen",
    )

    nodes_to_start = [robot_state_publisher_node, gz_spawn_entity, gz_ros2_bridge]

    if sensor == "camera":
        nodes_to_start.append(
            Node(
                package="ros_gz_image",
                executable="image_bridge",
                namespace=namespace,
                arguments=[f"/{namespace}/camera/image_raw"],
                output="screen",
            )
        )

    return nodes_to_start


def generate_launch_description():
    declared_arguments = [
        DeclareLaunchArgument("x", default_value="0"),
        DeclareLaunchArgument("y", default_value="0"),
        DeclareLaunchArgument("z", default_value="0"),
        DeclareLaunchArgument("R", default_value="0"),
        DeclareLaunchArgument("P", default_value="0"),
        DeclareLaunchArgument("Y", default_value="0"),
        DeclareLaunchArgument("sensor", default_value="laser"),
        DeclareLaunchArgument("noise", default_value="none"),
        DeclareLaunchArgument("namespace", default_value="turtlebot3"),
        DeclareLaunchArgument("entity", default_value="turtlebot3"),
    ]

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
