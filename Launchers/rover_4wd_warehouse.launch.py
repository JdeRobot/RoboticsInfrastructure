import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    AppendEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    ros_gz_sim_pkg = get_package_share_directory("ros_gz_sim")
    custom_share = get_package_share_directory("custom_robots")

    package_dir = custom_share

    urdf_file = os.path.join(custom_share, "urdf", "rover_4wd.urdf")

    bridge_yaml = os.path.join(custom_share, "config", "ros_gz_bridge.yaml")

    gazebo_models_path = os.path.join(package_dir, "models")

    world_file_name = "rover4wd_warehouse.world"
    worlds_dir = "/opt/jderobot/Worlds"
    world_path = os.path.join(worlds_dir, world_file_name)

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

    gz_sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_pkg, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": ["-r -s -v4 ", world_path],
            "on_exit_shutdown": "true",
        }.items(),
    )

    world_entity_cmd = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-name", "world", "-file", world_path],
        output="screen",
    )

    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic",
            "/robot_description",
            "-name",
            "rover_4wd",
            "-allow_renaming",
            "true",
            "-z",
            "0.15",
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

    ld.add_action(SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", gazebo_models_path))

    set_env_vars_resources = AppendEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH",
        os.path.join(package_dir, "models"),
    )
    ld.add_action(set_env_vars_resources)

    ld.add_action(gz_sim_launch)
    ld.add_action(world_entity_cmd)
    ld.add_action(robot_state_publisher_node)
    ld.add_action(gz_spawn_entity)
    ld.add_action(gz_ros2_bridge)

    return ld
