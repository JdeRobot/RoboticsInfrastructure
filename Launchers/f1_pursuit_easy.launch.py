import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    ros_gz_sim = get_package_share_directory("ros_gz_sim")

    # How fast the rival drives, one launcher per level
    level = "easy"

    world_file_name = "f1_pursuit.world"
    worlds_dir = "/opt/jderobot/Scenes"
    world_path = os.path.join(worlds_dir, world_file_name)

    gazebo_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": ["-s -v4 ", world_path],
            "on_exit_shutdown": "true",
        }.items(),
    )

    world_entity_cmd = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-name", "world", "-file", world_path],
        output="screen",
    )

    gz_ros2_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
        ],
        output="screen",
    )

    # Latched, because the rival is started well after the world is
    level_cmd = ExecuteProcess(
        cmd=[
            "ros2",
            "topic",
            "pub",
            "--qos-durability",
            "transient_local",
            "/f1_pursuit/level",
            "std_msgs/msg/String",
            f"data: {level}",
        ],
        output="screen",
    )

    ld = LaunchDescription()
    ld.add_action(gazebo_server)
    ld.add_action(world_entity_cmd)
    ld.add_action(gz_ros2_bridge)
    ld.add_action(level_cmd)

    return ld
