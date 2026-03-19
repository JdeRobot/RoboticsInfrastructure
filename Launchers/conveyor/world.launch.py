import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable, AppendEnvironmentVariable
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    custom_pkg = get_package_share_directory("custom_robots")
    models_path = os.path.join(custom_pkg, "models")

    world_path = "/opt/jderobot/Worlds/conveyor_world.world"

    gz_env = {
        "GZ_SIM_RESOURCE_PATH": models_path,
        "GZ_SIM_SYSTEM_PLUGIN_PATH": "/opt/ros/humble/lib",
        "LD_LIBRARY_PATH": "/opt/ros/humble/lib:/usr/lib/x86_64-linux-gnu",
        "DISPLAY": ":2",
    }

    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-s", "-r", "-v", "4", world_path],
        output="screen",
        additional_env=gz_env,
        shell=False,
    )

    ld = LaunchDescription()

    ld.add_action(
        SetEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH",
            models_path
        )
    )

    ld.add_action(
        AppendEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH",
            models_path
        )
    )

    ld.add_action(gazebo)

    return ld