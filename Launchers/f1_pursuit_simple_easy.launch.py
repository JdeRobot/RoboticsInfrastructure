import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    ros_gz_sim = get_package_share_directory("ros_gz_sim")

    # Circuit and rival speed, one launcher per circuit and level
    circuit = "simple_circuit"
    level = "easy"

    world_file_name = "f1_pursuit_simple.world"
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
    race_cmds = [
        ExecuteProcess(
            cmd=[
                "ros2",
                "topic",
                "pub",
                "--qos-durability",
                "transient_local",
                topic,
                "std_msgs/msg/String",
                f"data: {value}",
            ],
            output="screen",
        )
        for topic, value in (
            ("/f1_pursuit/circuit", circuit),
            ("/f1_pursuit/level", level),
        )
    ]

    ld = LaunchDescription()
    ld.add_action(gazebo_server)
    ld.add_action(world_entity_cmd)
    ld.add_action(gz_ros2_bridge)
    for cmd in race_cmds:
        ld.add_action(cmd)

    return ld
