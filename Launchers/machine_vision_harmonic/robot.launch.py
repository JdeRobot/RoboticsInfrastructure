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

    gz_ros2_control_install = "/home/ws/install"
    gz_lib_path = os.path.join(gz_ros2_control_install, "gz_ros2_control", "lib")

    warehouse_models_path = os.path.join(robotiq_pkg_share_dir, "world", "models")
    ur5_share_parent = os.path.dirname(pkg_share_dir)
    robotiq_share_parent = os.path.dirname(robotiq_pkg_share_dir)

    resource_path = (
        ur5_share_parent + ":" + robotiq_share_parent + ":" + warehouse_models_path
    )

    gz_env = {
        "GZ_SIM_RESOURCE_PATH": resource_path,
        "GZ_SIM_SYSTEM_PLUGIN_PATH": (
            "/home/ws/install/gz_link_attacher/lib:"
            + gz_lib_path
            + ":/opt/ros/humble/lib"
        ),
        "LD_LIBRARY_PATH": "/home/ws/install/gz_link_attacher/lib:"
        + gz_lib_path
        + ":/opt/ros/humble/lib:/usr/lib/x86_64-linux-gnu:"
        + os.environ.get("LD_LIBRARY_PATH", ""),
        "DISPLAY": ":2",
    }

    declared_arguments = [
        DeclareLaunchArgument("launch_rviz", default_value="true"),
    ]

    xacro_file = os.path.join(
        pkg_share_dir,
        "urdf",
        "ur5_machine_vision.urdf.xacro"
    )

    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "sim_gz": "true"
        },
    ).toxml()

    robot_description = {"robot_description": robot_description_content}

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    world_file = "/opt/jderobot/Worlds/machine_vision_harmonic.world"

    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-s", "-r", "-v", "4", world_file],
        output="screen",
        additional_env=gz_env,
        shell=False,
    )

    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic", "robot_description",
            "-name", "ur5",
            "-allow_renaming", "true",
            "-x", "0.0",
            "-y", "0.0",
            "-z", "0.9",
        ],
        output="screen",
    )

    static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0", "0", "0.9", "0", "0", "0", "world", "base_link"],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    jsb = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
    )

    traj = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_trajectory_controller", "-c", "/controller_manager"],
    )

    delay_spawn = TimerAction(period=5.0, actions=[spawn_entity])

    delay_js = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_entity,
            on_exit=[jsb],
        )
    )

    delay_traj = RegisterEventHandler(
        OnProcessExit(
            target_action=jsb,
            on_exit=[traj],
        )
    )

    return LaunchDescription(
        declared_arguments
        + [
            gazebo,
            robot_state_publisher,
            static_tf,
            clock_bridge,
            delay_spawn,
            delay_js,
            delay_traj,
        ]
    )