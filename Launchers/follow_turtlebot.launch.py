import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    ros_gz_sim = get_package_share_directory("ros_gz_sim")

    world_file_name = "follow_turtlebot.world"
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

    # The turtlebot is spawned here directly, not through the robots table, RAM only
    # launches one robot per world and that slot is reserved for the drone the
    # exercise's HAL.py expects (see database/worlds.sql robot 11 on world 78)
    turtlebot_spawn = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            "/home/ws/src/CustomRobots/turtlebot3/launch/turtlebot3.launch.py"
        ),
        launch_arguments={
            "x": "7.0",
            "y": "-4.0",
            "z": "0.1",
            "Y": "2.76",
            "sensor": "laser",
            "marker": "true",
            "namespace": "turtlebot3",
        }.items(),
    )

    # Drives the turtlebot around the patrol waypoints, the drone has no control over it
    turtlebot_patrol = ExecuteProcess(
        cmd=["python3", "/home/ws/src/CustomRobots/turtlebot3/patrol_turtlebot.py"],
        output="screen",
    )

    ld = LaunchDescription()
    ld.add_action(gazebo_server)
    ld.add_action(world_entity_cmd)
    ld.add_action(gz_ros2_bridge)
    ld.add_action(turtlebot_spawn)
    ld.add_action(turtlebot_patrol)

    return ld
