import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration, Command, IfElseSubstitution
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def launch_setup(context):
    use_sim_time = LaunchConfiguration("use_sim_time", default="true")
    x = LaunchConfiguration("x", default="0")
    y = LaunchConfiguration("y", default="0")
    z = LaunchConfiguration("z", default="0")
    R = LaunchConfiguration("R", default="0")
    P = LaunchConfiguration("P", default="0")
    Y = LaunchConfiguration("Y", default="0")
    sensor = LaunchConfiguration("sensor", default="camera")
    mode = LaunchConfiguration("mode", default="holo")

    package_dir = get_package_share_directory("custom_robots")

    nodes_to_start = []

    f1_sensor = "cam"
    f1_model = "holo"

    if sensor.perform(context) == "laser":
        f1_sensor = "laser"

    if mode.perform(context) == "ackermann":
        f1_model = "ackermann"

    urdf_file = os.path.join(package_dir, "urdf", f"f1_{f1_model}_{f1_sensor}.urdf")
    bridge_yaml = os.path.join(package_dir, "params", "f1_renault.yaml")

    robot_description = ParameterValue(
        Command(["xacro", " ", urdf_file]),
        value_type=str,
    )

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {"use_sim_time": use_sim_time, "robot_description": robot_description}
        ],
    )

    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic",
            "/robot_description",
            "-name",
            "f1",
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
        arguments=["--ros-args", "-p", f"config_file:={bridge_yaml}"],
        output="screen",
    )

    nodes_to_start.append(robot_state_publisher_node)
    nodes_to_start.append(gz_spawn_entity)
    nodes_to_start.append(gz_ros2_bridge)

    # Sensor deppending on sensor arguments
    if f1_sensor == "cam":
        gz_ros2_image_bridge = Node(
            package="ros_gz_image",
            executable="image_bridge",
            arguments=["/cam_f1_left/image_raw"],
            output="screen",
        )
        nodes_to_start.append(gz_ros2_image_bridge)

    return nodes_to_start


def generate_launch_description():
    declared_arguments = []

    # Add any entry parameter
    declared_arguments.append(DeclareLaunchArgument("x", default_value="0"))
    declared_arguments.append(DeclareLaunchArgument("y", default_value="0"))
    declared_arguments.append(DeclareLaunchArgument("z", default_value="0"))
    declared_arguments.append(DeclareLaunchArgument("R", default_value="0"))
    declared_arguments.append(DeclareLaunchArgument("P", default_value="0"))
    declared_arguments.append(DeclareLaunchArgument("Y", default_value="0"))
    declared_arguments.append(DeclareLaunchArgument("sensor", default_value="camera"))
    declared_arguments.append(DeclareLaunchArgument("mode", default_value="holo"))

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
