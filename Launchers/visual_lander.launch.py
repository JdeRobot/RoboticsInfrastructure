import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    ros_gz_sim = get_package_share_directory("ros_gz_sim")

    world_file_name = "visual_lander.world"
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

    # The car is plain geometry included straight in the world (it is not a
    # robot with its own launch.py, see database/worlds.sql), so its
    # cmd_vel/odom topics need their own bridge here.
    car_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/car/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry",
            "/car/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist",
        ],
        output="screen",
    )

    ld = LaunchDescription()
    ld.add_action(gazebo_server)
    ld.add_action(world_entity_cmd)
    ld.add_action(gz_ros2_bridge)
    ld.add_action(car_bridge)

    return ld
