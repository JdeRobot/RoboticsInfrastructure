import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():

    ros_gz_sim = get_package_share_directory("ros_gz_sim")
    package_dir = get_package_share_directory("custom_robots")

    world_file_name = "reduced_hospital_harmonic.world"
    world_path = os.path.join(
        package_dir,
        "worlds",
        world_file_name
    )

    gazebo_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": f"-r -v4 {world_path}"
        }.items(),
    )

    ld = LaunchDescription()

    ld.add_action(
        SetEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH",
            os.path.join(package_dir)
        )
    )

    ld.add_action(gazebo_server)

    return ld