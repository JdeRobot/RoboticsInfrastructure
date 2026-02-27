import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    model_folder = "amazon_robot_harmonic"

    sdf_path = os.path.join(
        get_package_share_directory("custom_robots"),
        "models",
        model_folder,
        "model.sdf",
    )

    x_pose = LaunchConfiguration("x_pose", default="0.0")
    y_pose = LaunchConfiguration("y_pose", default="0.0")
    z_pose = LaunchConfiguration("z_pose", default="0.5")
    roll = LaunchConfiguration("R", default="0.0")
    pitch = LaunchConfiguration("P", default="0.0")
    yaw = LaunchConfiguration("Y", default="0.0")

    spawn_robot_cmd = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name", "amazon_robot",
            "-file", sdf_path,
            "-x", x_pose,
            "-y", y_pose,
            "-z", z_pose,
            "-R", roll,
            "-P", pitch,
            "-Y", yaw,
        ],
        output="screen",
    )

    bridge_params = os.path.join(
        get_package_share_directory("custom_robots"),
        "params",
        "amazon_robot_harmonic.yaml",
    )

    bridge_cmd = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["--ros-args", "-p", f"config_file:={bridge_params}"],
        output="screen",
    )

    ld = LaunchDescription()

    ld.add_action(DeclareLaunchArgument("x_pose", default_value="1.0"))
    ld.add_action(DeclareLaunchArgument("y_pose", default_value="-1.5"))
    ld.add_action(DeclareLaunchArgument("z_pose", default_value="0.1"))
    ld.add_action(DeclareLaunchArgument("R", default_value="0.0"))
    ld.add_action(DeclareLaunchArgument("P", default_value="0.0"))
    ld.add_action(DeclareLaunchArgument("Y", default_value="0.0"))

    ld.add_action(spawn_robot_cmd)
    ld.add_action(bridge_cmd)

    return ld
