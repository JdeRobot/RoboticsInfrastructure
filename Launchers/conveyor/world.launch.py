import os

from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable


def generate_launch_description():

    world_path = "/opt/jderobot/Worlds/conveyor_world.world"

    # ==================================================
    # PLUGIN PATHS
    # ==================================================

    gz_ros2_control_path = "/home/ws/install/gz_ros2_control/lib"
    gz_link_attacher_path = "/home/ws/install/gz_link_attacher/lib"
    conveyor_plugin_path = "/home/ws/install/conveyor_belt_plugin/lib"

    gz_plugin_path = (
        conveyor_plugin_path
        + ":"
        + gz_link_attacher_path
        + ":"
        + gz_ros2_control_path
        + ":"
        + "/opt/ros/humble/lib"
    )

    # ==================================================
    # RESOURCE PATHS
    # ==================================================

    resource_path = (
        "/home/ws/src/CustomRobots"
    )

    set_resource_path = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=resource_path,
    )

    set_gz_plugin_path = SetEnvironmentVariable(
        name="GZ_SIM_SYSTEM_PLUGIN_PATH",
        value=gz_plugin_path,
    )

    existing_ld = os.environ.get("LD_LIBRARY_PATH", "")

    set_ld_library_path = SetEnvironmentVariable(
        name="LD_LIBRARY_PATH",
        value=gz_plugin_path
        + ":/usr/lib/x86_64-linux-gnu:"
        + existing_ld,
    )

    # ==================================================
    # GAZEBO
    # ==================================================

    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-r", "-v", "4", world_path],
        output="screen",
        shell=False,
    )

    return LaunchDescription([
        set_gz_plugin_path,
        set_ld_library_path,
        set_resource_path,
        gazebo,
    ])