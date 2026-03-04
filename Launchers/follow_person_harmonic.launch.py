import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable, AppendEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():

    package_dir = get_package_share_directory("custom_robots")
    ros_gz_sim = get_package_share_directory("ros_gz_sim")

    gazebo_models_path = os.path.join(package_dir, "models")

    world_file_name = "reduced_hospital_harmonic.world"
    worlds_dir = "/opt/jderobot/Worlds"
    world_path = os.path.join(worlds_dir, world_file_name)

    gazebo_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": [f"-r -s -v4 {world_path}"],
            "on_exit_shutdown": "true",
        }.items(),
    )

    ld = LaunchDescription()

    ld.add_action(SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", gazebo_models_path))
    ld.add_action(AppendEnvironmentVariable("GZ_SIM_RESOURCE_PATH", gazebo_models_path))
    ld.add_action(gazebo_server)

    return ld