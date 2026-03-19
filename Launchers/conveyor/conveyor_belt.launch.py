import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    ros_gz_sim = get_package_share_directory("ros_gz_sim")

    world_path = "/opt/jderobot/Worlds/conveyor_world.world"

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": ["-r", "-v4", world_path],
        }.items(),
    )

    return LaunchDescription([gazebo])