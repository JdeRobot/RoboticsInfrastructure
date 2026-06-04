from launch.actions import (
    IncludeLaunchDescription,
    DeclareLaunchArgument,
    SetEnvironmentVariable,
)
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch import LaunchDescription
from launch_ros.actions import Node

import os
import xacro
import yaml
from ament_index_python.packages import get_package_share_directory
from launch.actions import DeclareLaunchArgument, OpaqueFunction


def load_file(package_name, file_path):
    pkg_path = get_package_share_directory(package_name)
    with open(os.path.join(pkg_path, file_path), "r") as f:
        return f.read()


def load_yaml(package_name, file_path):
    pkg_path = get_package_share_directory(package_name)
    with open(os.path.join(pkg_path, file_path), "r") as f:
        return yaml.safe_load(f)


def launch_setup(context):
    x = LaunchConfiguration("x")
    y = LaunchConfiguration("y")
    z = LaunchConfiguration("z")
    R = LaunchConfiguration("R")
    P = LaunchConfiguration("P")
    Y = LaunchConfiguration("Y")
    gz_sensor = LaunchConfiguration("sensor")

    sensor = gz_sensor.perform(context)

    nodes = []

    # =========================
    # ROBOT DESCRIPTION (URDF)
    # =========================
    xacro_file = os.path.join(
        get_package_share_directory("ros2srrc_ur3_gazebo"),
        "urdf",
        "ur3_robotiq_2f85.urdf.xacro",
    )

    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "bringup": "false",
            "hmi": "false",
            "robot_ip": "0.0.0.0",
            "EE": "true",
            "EE_name": "robotiq_2f85",
            "camera": "true" if sensor == "camera" else "false",
            "script_filename": "none",
            "input_recipe_filename": "none",
            "output_recipe_filename": "none",
        },
    ).toxml()

    robot_description = {"robot_description": robot_description_content}

    # =========================
    # ENVIROMENT
    # =========================

    gz_ros2_control_path = "/home/ws/install/gz_ros2_control/lib"
    gz_link_attacher_path = "/home/ws/install/gz_link_attacher/lib"

    gz_plugin_path = (
        gz_link_attacher_path + ":" + gz_ros2_control_path + ":" + "/opt/ros/humble/lib"
    )

    resource_path = (
        os.path.dirname(
            get_package_share_directory("ros2srrc_ur3_gazebo")
        )
        + ":"
        + os.path.dirname(
            get_package_share_directory("ros2srrc_robots")
        )
        + ":"
        + os.path.dirname(
            get_package_share_directory("ros2srrc_endeffectors")
        )
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

    # =========================
    # SRDF (SEMANTIC)
    # =========================
    robot_description_semantic = {
        "robot_description_semantic": load_file(
            "ros2srrc_ur3_moveit2",
            "config/ur3robotiq_2f85.srdf"
        )
    }

    # =========================
    # NODES
    # =========================

    move = Node(
        package="ros2srrc_execution",
        executable="move",
        name="move_action_server",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            {"use_sim_time": True},
            {"ROB_PARAM": "ur3"},
            {"EE_PARAM": "robotiq_2f85"},
        ],
    )

    robmove = Node(
        package="ros2srrc_execution",
        executable="robmove",
        name="Robmove",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            {"use_sim_time": True},
            {"ROB_PARAM": "ur3"},
        ],
    )

    robpose = Node(
        package="ros2srrc_execution",
        executable="robpose",
        name="robpose",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            {"use_sim_time": True},
            {"ROB_PARAM": "ur3"},
        ],
    )

    nodes.append(move)
    nodes.append(robmove)
    nodes.append(robpose)

    # =========================
    # CORE NODES
    # =========================

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[robot_description, {"use_sim_time": True}],
        output="screen",
    )

    static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=[x, y, z, R, P, Y, "world", "base_link"],
    )

    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic",
            "robot_description",
            "-name",
            "ur3",
            "-x",
            x,
            "-y",
            y,
            "-z",
            z,
            "-R",
            R,
            "-P",
            P,
            "-Y",
            Y,
        ],
        output="screen",
    )

    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock]"],
        parameters=[{"use_sim_time": True}],
    )

    nodes.append(robot_state_publisher)
    nodes.append(static_tf)
    nodes.append(spawn_robot)
    nodes.append(clock_bridge)

    if sensor == "camera":
        camera_bridge = Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            arguments=[
                "/hand_camera/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo",
                "/base_camera/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo",
            ],
            output="screen",
        )

        gz_ros2_image_bridge = Node(
            package="ros_gz_image",
            executable="image_bridge",
            arguments=["/hand_camera/image"],
            output="screen",
        )

        gz_ros2_base_image_bridge = Node(
            package="ros_gz_image",
            executable="image_bridge",
            arguments=["/base_camera/image"],
            output="screen",
        )

        nodes.append(camera_bridge)
        nodes.append(gz_ros2_image_bridge)
        nodes.append(gz_ros2_base_image_bridge)

    # =========================
    # CONTROLLERS
    # =========================

    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
    )

    joint_trajectory_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_trajectory_controller"],
    )

    gripper_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gripper_controller"],
    )

    nodes.append(joint_state_broadcaster)
    nodes.append(joint_trajectory_controller)
    nodes.append(gripper_controller)

    # =========================
    # LAUNCH
    # =========================

    return nodes


def generate_launch_description():
    declared_arguments = [
        DeclareLaunchArgument("x", default_value="0.5"),
        DeclareLaunchArgument("y", default_value="0"),
        DeclareLaunchArgument("z", default_value="0"),
        DeclareLaunchArgument("R", default_value="0"),
        DeclareLaunchArgument("P", default_value="0"),
        DeclareLaunchArgument("Y", default_value="0"),
        DeclareLaunchArgument("sensor", default_value="none"),
    ]

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
