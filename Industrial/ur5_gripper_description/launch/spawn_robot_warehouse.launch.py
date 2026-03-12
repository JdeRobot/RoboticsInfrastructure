import os
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    RegisterEventHandler,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import xacro


def generate_launch_description():

    pkg_share_dir = get_package_share_directory("ur5_gripper_description")
    robotiq_pkg_share_dir = get_package_share_directory("robotiq_description")

    ################################################
    # Paths
    ################################################

    gz_ros2_control_install = "/home/ws/install"
    gz_ros2_control_lib = os.path.join(gz_ros2_control_install, "gz_ros2_control", "lib")

    # LINK ATTACHER PLUGIN
    link_attacher_lib = "/home/ws/install/gz_link_attacher/lib"

    warehouse_models_path = os.path.join(robotiq_pkg_share_dir, "world", "models")

    ur5_share_parent = os.path.dirname(pkg_share_dir)
    robotiq_share_parent = os.path.dirname(robotiq_pkg_share_dir)

    ################################################
    # Gazebo resource path
    ################################################

    resource_path = (
        ur5_share_parent
        + ":"
        + robotiq_share_parent
        + ":"
        + warehouse_models_path
    )

    ################################################
    # Gazebo plugin path
    ################################################

    plugin_path = (
        link_attacher_lib
        + ":"
        + gz_ros2_control_lib
        + ":/opt/ros/humble/lib"
    )

    ################################################
    # Environment for Gazebo
    ################################################

    gz_env = {
        "GZ_SIM_RESOURCE_PATH": resource_path,
        "GZ_SIM_SYSTEM_PLUGIN_PATH": plugin_path,
        "LD_LIBRARY_PATH": plugin_path + ":/usr/lib/x86_64-linux-gnu",
        "DISPLAY": ":2",
    }

    print("======================================")
    print("GAZEBO RESOURCE PATH:")
    print(resource_path)
    print("GAZEBO PLUGIN PATH:")
    print(plugin_path)
    print("======================================")

    ################################################
    # Launch arguments
    ################################################

    declared_arguments = [
        DeclareLaunchArgument("ur_type", default_value="ur5"),
        DeclareLaunchArgument("launch_rviz", default_value="true"),
    ]

    ################################################
    # Robot description
    ################################################

    xacro_file = os.path.join(pkg_share_dir, "urdf", "ur5_robotiq85_gripper.urdf.xacro")
    controllers_file = os.path.join(pkg_share_dir, "config", "ur5_controllers.yaml")

    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "ur_type": "ur5",
            "name": "ur",
            "prefix": "",
            "use_fake_hardware": "false",
            "sim_gazebo": "false",
            "sim_gz": "true",
            "simulation_controllers": controllers_file,
        },
    ).toxml()

    robot_description = {"robot_description": robot_description_content}

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    ################################################
    # World
    ################################################

    world_file = os.path.join(
        robotiq_pkg_share_dir,
        "world",
        "warehouse_arm_harmonic.world"
    )

    ################################################
    # Gazebo server
    ################################################

    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-s", "-r", "-v", "4", world_file],
        output="screen",
        additional_env=gz_env,
        shell=False,
    )

    ################################################
    # Spawn robot
    ################################################

    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic", "robot_description",
            "-name", "ur5_robotiq",
            "-allow_renaming", "true",
            "-x", "0.0",
            "-y", "0.0",
            "-z", "0.9",
            "-R", "0.0",
            "-P", "0.0",
            "-Y", "0.0",
        ],
        output="screen",
    )

    ################################################
    # Static TF
    ################################################

    static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0", "0", "0.9", "0", "0", "0", "world", "base_link"],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    ################################################
    # Clock bridge
    ################################################

    gz_ros2_bridge_clock = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    ################################################
    # Spawn delay
    ################################################

    delay_spawn = TimerAction(period=5.0, actions=[spawn_entity])

    ################################################
    # Launch description
    ################################################

    return LaunchDescription(
        declared_arguments
        + [
            gazebo,
            robot_state_publisher,
            static_tf,
            gz_ros2_bridge_clock,
            delay_spawn,
        ]
    )