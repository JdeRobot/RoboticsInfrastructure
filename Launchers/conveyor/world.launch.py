import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    package_dir = get_package_share_directory("custom_robots")

    world_path = os.path.join(package_dir, "worlds", "mi_mundo.world")

    gazebo_models_path = os.path.join(package_dir, "models")

    set_env = SetEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH",
        gazebo_models_path
    )

    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-r", "-v", "4", world_path],
        output="screen"
    )

    return LaunchDescription([
        set_env,
        gazebo
    ])