import os
from launch import LaunchDescription
from launch.actions import (
    ExecuteProcess,
    SetEnvironmentVariable,
    AppendEnvironmentVariable,
)
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node


def generate_launch_description():

    package_dir = get_package_share_directory("custom_robots")
    robotiq_description_pkg = get_package_share_directory("robotiq_description")
    ur5_gripper_pkg = get_package_share_directory("ur5_gripper_description")

    robotiq_pkg_share_dir = robotiq_description_pkg
    warehouse_models_path = os.path.join(robotiq_pkg_share_dir, "world", "models")

    ur5_share_parent = os.path.dirname(ur5_gripper_pkg)
    robotiq_share_parent = os.path.dirname(robotiq_pkg_share_dir)

    # =========================
    # PATHS
    # =========================

    world_path = "/opt/jderobot/Worlds/machine_vision_harmonic.world"   

    gazebo_models_path = os.path.join(package_dir, "models")

    gz_ros2_control_install = "/home/ws/install"
    gz_lib_path = os.path.join(gz_ros2_control_install, "gz_ros2_control", "lib")

    gz_link_attacher_lib = "/home/ws/install/gz_link_attacher/lib"

    custom_models_path = "/home/dev_ws/src/IndustrialRobots/ros2_SimRealRobotControl/packages/ur5/ros2srrc_ur5_gazebo/models"

    resource_path = (
        ur5_share_parent + ":" +
        robotiq_share_parent + ":" +
        warehouse_models_path + ":" +
        custom_models_path
    )

    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-s", "-r", "-v", "4", world_path],
        output="screen",
        shell=False,
    )

    ld = LaunchDescription()

    existing_ld = os.environ.get("LD_LIBRARY_PATH", "")

    ld.add_action(
        SetEnvironmentVariable(
            name="LD_LIBRARY_PATH",
            value=(
                gz_lib_path + ":"
                + gz_link_attacher_lib + ":"
                + "/home/ws/install/lib:"
                + "/home/ws/install/linkattacher_msgs/lib:"
                + "/opt/ros/humble/lib:"
                + existing_ld
            ),
        )
    )

    ld.add_action(
        SetEnvironmentVariable(
            name="GZ_SIM_SYSTEM_PLUGIN_PATH",
            value=(
                "/usr/lib/x86_64-linux-gnu/gz-sim-8/plugins:"
                "/usr/lib/x86_64-linux-gnu/gz-sim-8/systems:"
                + gz_lib_path + ":"
                + gz_link_attacher_lib + ":"
                + "/opt/ros/humble/lib"
            ),
        )
    )

    ld.add_action(
        SetEnvironmentVariable(
            name="GZ_SIM_RESOURCE_PATH",
            value=resource_path,
        )
    )

    ld.add_action(gazebo)

    return ld