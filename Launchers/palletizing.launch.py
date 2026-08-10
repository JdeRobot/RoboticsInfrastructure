#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable, TimerAction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    world_file_name = "palletizing_arm_harmonic.world"
    worlds_dir = "/opt/jderobot/Scenes"
    world_path = os.path.join(worlds_dir, world_file_name)

    package_dir = get_package_share_directory("custom_robots")
    gazebo_models_path = os.path.join(package_dir, "models")

    # Paths. The apt ros-humble-gz-ros2-control is built against Ignition Fortress
    # (gz-sim6, exports IgnitionPluginHook) — it CANNOT load under Gazebo Harmonic
    # (gz-sim8), which needs GzPluginHook, so the controller_manager never starts.
    # The workspace build of gz_ros2_control, compiled with GZ_VERSION=harmonic,
    # exports GzPluginHook and links libgz-sim8 — it MUST come first on the path so
    # gz picks it over the broken apt one. gz_link_attacher is also workspace-built.
    from ament_index_python.packages import get_package_prefix
    try:
        gz_link_attacher_path = os.path.join(get_package_prefix("gz_link_attacher"), "lib")
    except:
        gz_link_attacher_path = "/home/ws/install/gz_link_attacher/lib"

    try:
        gz_ros2_control_path = os.path.join(get_package_prefix("gz_ros2_control"), "lib")
    except:
        gz_ros2_control_path = "/home/ws/install/gz_ros2_control/lib"

    gz_plugin_path = (
        gz_ros2_control_path + ":" + gz_link_attacher_path + ":" + "/opt/ros/humble/lib"
    )

    resource_path = (
        os.path.dirname(get_package_share_directory("ros2srrc_ur5_gazebo"))
        + ":"
        + os.path.dirname(get_package_share_directory("robotiq_description"))
        + ":"
        + gazebo_models_path
    )

    set_resource_path = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH", value=resource_path
    )

    set_gz_plugin_path = SetEnvironmentVariable(
        name="GZ_SIM_SYSTEM_PLUGIN_PATH", value=gz_plugin_path
    )

    existing_ld = os.environ.get("LD_LIBRARY_PATH", "")

    set_ld_library_path = SetEnvironmentVariable(
        name="LD_LIBRARY_PATH",
        value=gz_plugin_path + ":/usr/lib/x86_64-linux-gnu:" + existing_ld,
    )

    gz = ExecuteProcess(
        cmd=["gz", "sim", "-r", "-v", "4", world_path],
        output="screen",
    )

    # YAML maps the differing ROS and Gazebo conveyor topic names.
    bridge_config = os.path.join(package_dir, "params", "conveyor_bridge.yaml")
    conveyor_speed_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="conveyor_speed_bridge",
        arguments=["--ros-args", "-p", f"config_file:={bridge_config}"],
        output="screen",
    )

    # Feeder owns conveyor speed and the spawn/ready/done lifecycle.
    task_config = os.path.join(package_dir, "config", "palletizing_task.yaml")
    box_spawner = Node(
        package="custom_robots",
        executable="box_spawner",
        name="box_spawner",
        output="screen",
        parameters=[
            {"use_sim_time": True},
            {"task_config": task_config},
        ],
    )

    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="clock_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
        ],
        output="screen",
    )

    # Give gz sim time to initialise before starting the bridge and spawner.
    delayed = TimerAction(
        period=5.0,
        actions=[conveyor_speed_bridge, box_spawner],
    )

    return LaunchDescription(
        [set_gz_plugin_path, set_ld_library_path, set_resource_path, gz, clock_bridge, delayed]
    )
