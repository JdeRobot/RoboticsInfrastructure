import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    custom_pkg = get_package_share_directory("custom_robots")
    ros_gz_sim = get_package_share_directory("ros_gz_sim")

    world_path = "/opt/jderobot/Worlds/conveyor_world.world"

    resource_path = custom_pkg + ":/usr/share/gz/gz-sim"

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": ["-r -v4 ", world_path],
            "on_exit_shutdown": "true",
            "gz_sim_resource_path": resource_path,
        }.items(),
    )

    ld = LaunchDescription()
    ld.add_action(gazebo)

    return ld