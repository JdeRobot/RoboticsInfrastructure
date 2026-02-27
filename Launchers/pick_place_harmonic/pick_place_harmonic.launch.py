import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():

    base_dir = os.path.dirname(__file__)

    world_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(base_dir, "world.launch.py")
        )
    )

    robot_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(base_dir, "robot.launch.py")
        )
    )

    return LaunchDescription([
        world_launch,
        robot_launch
    ])