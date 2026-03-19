import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    custom_pkg = get_package_share_directory("custom_robots")

    models_path = custom_pkg

    world_path = "/opt/jderobot/Worlds/conveyor_world.world"

    plugin_path = os.path.join(
        os.path.expanduser("~"),
        "ws/install/conveyor_belt_plugin/lib"
    )

    gz_env = {
        "GZ_SIM_RESOURCE_PATH": models_path,
        "GZ_SIM_SYSTEM_PLUGIN_PATH": plugin_path + ":/opt/ros/humble/lib",
        "LD_LIBRARY_PATH": os.environ.get("LD_LIBRARY_PATH", "")
        + ":" + plugin_path + ":/opt/ros/humble/lib:/usr/lib/x86_64-linux-gnu",
        "DISPLAY": os.environ.get("DISPLAY", ":0"),
    }

    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-r", "-v", "4", world_path],
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

    ld.add_action(gazebo)

    return ld