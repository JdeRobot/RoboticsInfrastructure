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

    custom_models_path = "/home/dev_ws/src/IndustrialRobots/ros2_SimRealRobotControl/packages/ur5/ros2srrc_ur5_gazebo/models"

    world_path = "/opt/jderobot/Worlds/machine_vision_harmonic.world"

    gazebo_models_path = os.path.join(package_dir, "models")

    gz_ros2_control_install = "/home/ws/install"
    gz_lib_path = os.path.join(gz_ros2_control_install, "gz_ros2_control", "lib")

    resource_path = (
        ur5_share_parent + ":" +
        robotiq_share_parent + ":" +
        warehouse_models_path + ":" +
        custom_models_path
    )

    gz_env = {
        "GZ_SIM_RESOURCE_PATH": resource_path,
        "GZ_SIM_SYSTEM_PLUGIN_PATH": gz_lib_path + ":/opt/ros/humble/lib",
        "LD_LIBRARY_PATH": gz_lib_path
        + ":/opt/ros/humble/lib:/usr/lib/x86_64-linux-gnu",
        "DISPLAY": os.environ.get("DISPLAY", ":0"),
    }

    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-s", "-r", "-v", "4", world_path],
        output="screen",
        additional_env=gz_env,
        shell=False,
    )

    world_entity_cmd = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-name", "world", "-file", world_path],
        output="screen",
    )

    ld = LaunchDescription()

    ld.add_action(
        SetEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH",
            gazebo_models_path + ":" + ur5_gripper_pkg + ":" + robotiq_description_pkg,
        )
    )

    ld.add_action(
        AppendEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH",
            gazebo_models_path + ":" + ur5_gripper_pkg + ":" + robotiq_description_pkg,
        )
    )

    ld.add_action(gazebo)
    ld.add_action(world_entity_cmd)

    return ld