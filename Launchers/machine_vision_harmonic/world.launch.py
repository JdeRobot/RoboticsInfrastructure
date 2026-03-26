import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess


def generate_launch_description():

    world_path = "/opt/jderobot/Worlds/machine_vision_harmonic.world"

    gz_ros2_control_install = "/home/ws/install"
    gz_lib_path = os.path.join(gz_ros2_control_install, "gz_ros2_control", "lib")

    gz_env = {
        "GZ_SIM_SYSTEM_PLUGIN_PATH": (
            "/home/ws/install/gz_link_attacher/lib:"
            + gz_lib_path +
            ":/opt/ros/humble/lib"
        ),
        "LD_LIBRARY_PATH": (
            "/home/ws/install/gz_link_attacher/lib:"
            + gz_lib_path +
            ":/opt/ros/humble/lib:/usr/lib/x86_64-linux-gnu:"
            + os.environ.get("LD_LIBRARY_PATH", "")
        ),
        "DISPLAY": os.environ.get("DISPLAY", ":0"),
    }

    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-r", "-v", "4", world_path],
        output="screen",
        additional_env=gz_env,
        shell=False,
    )

    return LaunchDescription([
        gazebo
    ])