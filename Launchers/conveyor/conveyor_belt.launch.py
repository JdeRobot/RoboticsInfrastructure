import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():

    base_dir = os.path.dirname(__file__)

    world = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(base_dir, "world.launch.py")
        )
    )

    robot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(base_dir, "robot.launch.py")
        )
    )

    spawner = Node(
        package="custom_robots",
        executable="spawn_sausage.py",
        name="box_spawner",
        output="screen"
    )

    return LaunchDescription([
        world,
        robot,
        spawner
    ])