#!/usr/bin/env python3

import os
import xacro

from launch import LaunchDescription
from launch.actions import TimerAction, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_share_dir = get_package_share_directory("ur5_gripper_description")

    # =========================
    # URDF (XACRO)
    # =========================

    xacro_file = os.path.join(
        pkg_share_dir, "urdf", "ur5_robotiq85_gripper.urdf.xacro"
    )

    controllers_file = os.path.join(
        pkg_share_dir, "config", "ur5_controllers.yaml"
    )

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

    # =========================
    # ROBOT STATE PUBLISHER 
    # =========================

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",  # evita duplicados raros
        output="screen",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    # =========================
    # SPAWN ENTITY
    # =========================

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
        ],
        output="screen",
    )

    # =========================
    # TF
    # =========================

    static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0", "0", "0.9", "0", "0", "0", "world", "base_link"],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    # =========================
    # CLOCK
    # =========================

    gz_ros2_bridge_clock = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    # =========================
    # CONTROLLERS
    # =========================

    load_joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
        ],
        output="screen",
    )

    load_joint_trajectory_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_trajectory_controller",
            "--param-file",
            controllers_file,
            "-c",
            "/controller_manager",
        ],
        output="screen",
    )

    load_gripper_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "gripper_controller",
            "--param-file",
            controllers_file,
            "-c",
            "/controller_manager",
        ],
        output="screen",
    )

    # =========================
    # DELAYS
    # =========================

    delay_spawn = TimerAction(period=3.0, actions=[spawn_entity])

    delay_jsb = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_entity,
            on_exit=[load_joint_state_broadcaster],
        )
    )

    delay_jtc = RegisterEventHandler(
        OnProcessExit(
            target_action=load_joint_state_broadcaster,
            on_exit=[load_joint_trajectory_controller],
        )
    )

    delay_gc = RegisterEventHandler(
        OnProcessExit(
            target_action=load_joint_trajectory_controller,
            on_exit=[load_gripper_controller],
        )
    )

    return LaunchDescription([
        robot_state_publisher,
        static_tf,
        gz_ros2_bridge_clock,

        delay_spawn,
        delay_jsb,
        delay_jtc,
        delay_gc,
    ])