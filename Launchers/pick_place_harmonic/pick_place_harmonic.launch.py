#!/usr/bin/env python3

import os
import xacro
import yaml

from launch import LaunchDescription
from launch.actions import ExecuteProcess, RegisterEventHandler, TimerAction
from launch.event_handlers import OnProcessExit
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def load_file(package_name, file_path):
    pkg_path = get_package_share_directory(package_name)
    with open(os.path.join(pkg_path, file_path), 'r') as f:
        return f.read()


def load_yaml(package_name, file_path):
    pkg_path = get_package_share_directory(package_name)
    with open(os.path.join(pkg_path, file_path), 'r') as f:
        return yaml.safe_load(f)


def generate_launch_description():

    # =========================
    # WORLD (HARMONIC)
    # =========================

    world_path = os.path.join(
        get_package_share_directory("robotiq_description"),
        "world",
        "warehouse_arm_harmonic.world"
    )

    gz = ExecuteProcess(
        cmd=["gz", "sim", "-r", "-v", "4", world_path],
        output="screen"
    )

    # =========================
    # ROBOT DESCRIPTION (CLAVE)
    # =========================

    xacro_file = "/home/ws/src/Industrial/ros2_SimRealRobotControl_gz/packages/ur5/ros2srrc_ur5_gazebo/urdf/ur5_robotiq_2f85.urdf.xacro"

    pkg_share_dir = get_package_share_directory("ur5_gripper_description")
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

    # =========================
    # SRDF + KINEMATICS
    # =========================

    robot_description_semantic = {
        "robot_description_semantic": load_file(
            "ur5_gripper_moveit_config",
            "srdf/ur5_robotiq.srdf"
        )
    }

    kinematics_yaml = {
        "robot_description_kinematics": load_yaml(
            "ur5_gripper_moveit_config",
            "config/kinematics.yaml"
        )
    }

    # =========================
    # ROBOT STATE PUBLISHER
    # =========================

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0", "0", "0.9", "0", "0", "0", "world", "base_link"],
        parameters=[{"use_sim_time": True}],
    )

    # =========================
    # SPAWN ROBOT (HARMONIC)
    # =========================

    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic", "robot_description",
            "-name", "ur5",
            "-x", "0.0",
            "-y", "0.0",
            "-z", "0.9",
        ],
        output="screen",
    )

    # =========================
    # CLOCK BRIDGE
    # =========================

    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        parameters=[{"use_sim_time": True}],
    )

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

    # =========================
    # MOVE GROUP (IGUAL QUE CLASSIC)
    # =========================

    move_group = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            {"use_sim_time": True},
        ],
    )

    # =========================
    # INTERFACES (CLÁSICO)
    # =========================

    common_params = [
        robot_description,
        robot_description_semantic,
        kinematics_yaml,
        {"use_sim_time": True},
        {"ROB_PARAM": "ur5"},
        {"EE_PARAM": "robotiq_2f85"},
        {"ENV_PARAM": "gazebo"},
    ]

    move_node = Node(
        package="ros2srrc_execution",
        executable="move",
        output="screen",
        parameters=common_params,
    )

    robmove_node = Node(
        package="ros2srrc_execution",
        executable="robmove",
        output="screen",
        parameters=common_params,
    )

    robpose_node = Node(
        package="ros2srrc_execution",
        executable="robpose",
        output="screen",
        parameters=common_params,
    )

    # =========================
    # SECUENCIA (CLAVE)
    # =========================

    return LaunchDescription([

        gz,
        robot_state_publisher,
        static_tf,
        clock_bridge,

        spawn_robot,

        RegisterEventHandler(
            OnProcessExit(
                target_action=spawn_robot,
                on_exit=[joint_state_broadcaster],
            )
        ),

        RegisterEventHandler(
            OnProcessExit(
                target_action=joint_state_broadcaster,
                on_exit=[joint_trajectory_controller],
            )
        ),

        RegisterEventHandler(
            OnProcessExit(
                target_action=joint_trajectory_controller,
                on_exit=[gripper_controller],
            )
        ),

        RegisterEventHandler(
            OnProcessExit(
                target_action=spawn_robot,
                on_exit=[
                    TimerAction(
                        period=2.0,
                        actions=[move_group],
                    )
                ],
            )
        ),

        RegisterEventHandler(
            OnProcessExit(
                target_action=spawn_robot,
                on_exit=[
                    TimerAction(
                        period=4.0,
                        actions=[move_node, robmove_node, robpose_node],
                    )
                ],
            )
        ),
    ])