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
    gz_namespace = LaunchConfiguration("namespace")
    gz_entity = LaunchConfiguration("entity")

    package_dir = get_package_share_directory("custom_robots")

    nodes_to_start = []

    sensor = gz_sensor.perform(context)
    namespace = gz_namespace.perform(context)
    entity = gz_entity.perform(context)

    # =========================
    # ROBOT DESCRIPTION (URDF)
    # =========================
    xacro_file = os.path.join(
        package_dir,
        "models",
        "vacuum_cleaner",
        "vacuum_cleaner.urdf.xacro",
    )

    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "camera": "true" if sensor == "camera" else "false",
            "laser": "true" if sensor == "laser" else "false",
            "namespace": namespace,
        },
    ).toxml()
    # if sensor == "camera":
    # else:
    #     # Temporary SDF load to fix bumpers from world. Just spawn bridge
    #     sdf_file = os.path.join(
    #         package_dir, "models", "vacuum_cleaner", "vacuum_cleaner.sdf"
    #     )
    #     with open(sdf_file, "r") as infp:
    #         robot_description_content = infp.read()

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
            f"/{namespace}/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist",
            f"/{namespace}/laser/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
            f"/{namespace}/events/center_bumper@ros_gz_interfaces/msg/Contacts[gz.msgs.Contacts",
            f"/{namespace}/events/right_bumper@ros_gz_interfaces/msg/Contacts[gz.msgs.Contacts",
            f"/{namespace}/events/left_bumper@ros_gz_interfaces/msg/Contacts[gz.msgs.Contacts",
        ],
        output="screen",
    )

    nodes_to_start.append(robot_state_publisher_node)
    nodes_to_start.append(gz_spawn_entity)
    nodes_to_start.append(gz_ros2_bridge)

    # Sensor deppending on sensor arguments
    if sensor == "camera":
        gz_ros2_image_bridge = Node(
            package="ros_gz_image",
            executable="image_bridge",
            namespace=gz_namespace,
            arguments=[f"/{namespace}/camera/image_raw"],
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
        DeclareLaunchArgument("sensor", default_value="laser"),
        DeclareLaunchArgument("namespace", default_value="vacuum_cleaner"),
        DeclareLaunchArgument("entity", default_value="vacuum_cleaner"),
    ]

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
