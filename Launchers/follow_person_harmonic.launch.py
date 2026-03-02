import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import SetEnvironmentVariable, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():

    world_file_name = "reduced_hospital_harmonic.world"

    worlds_dir = "/opt/jderobot/Worlds"
    world_path = os.path.join(worlds_dir, world_file_name)

    ros_gz_sim = get_package_share_directory("ros_gz_sim")

    gazebo_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": ["-r -s ", world_path],
            "on_exit_shutdown": "true",
        }.items(),
    )

    ld = LaunchDescription()

    ld.add_action(
        SetEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH",
            "/opt/jderobot/Worlds"
        )
    )

    ld.add_action(gazebo_server)

    return ld