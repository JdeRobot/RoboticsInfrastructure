import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    package_dir = get_package_share_directory("custom_robots")

    urdf_file = os.path.join(package_dir, "urdf", "f1.urdf")
    bridge_yaml = os.path.join(package_dir, "params", "f1_renault.yaml")

    use_sim_time = LaunchConfiguration("use_sim_time", default="true")

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
            str(53.462),
            "-y",
            str(-10.734),
            "-z",
            str(0.004),
            "-R",
            str(0),
            "-P",
            str(0),
            "-Y",
            str(-1.57),
        ],
        output="screen",
    )

    gz_ros2_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["--ros-args", "-p", f"config_file:={bridge_yaml}"],
        output="screen",
    )

    ld = LaunchDescription()

    # Add any actions
    ld.add_action(robot_state_publisher_node)
    ld.add_action(gz_spawn_entity)
    ld.add_action(gz_ros2_bridge)

    return ld
