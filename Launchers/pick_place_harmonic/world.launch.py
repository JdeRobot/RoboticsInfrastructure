import os
from launch import LaunchDescription
from launch.actions import AppendEnvironmentVariable
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    package_dir = get_package_share_directory("custom_robots")
    robotiq_description_pkg = get_package_share_directory("robotiq_description")
    ur5_gripper_pkg = get_package_share_directory("ur5_gripper_description")

    gazebo_models_path = os.path.join(package_dir, "models")

    gz_resource_path = (
        ":" + gazebo_models_path +
        ":" + ur5_gripper_pkg +
        ":" + robotiq_description_pkg
    )

    append_env = AppendEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH",
        gz_resource_path,
    )

    return LaunchDescription([
        append_env
    ])