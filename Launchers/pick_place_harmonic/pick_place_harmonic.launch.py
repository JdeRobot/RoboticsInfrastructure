Este es el launcher que estoy usando:
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
    # WORLD
    # =========================

    world_path = os.path.join(
        get_package_share_directory("robotiq_description"),
        "world",
        "warehouse_arm_harmonic.world"
    )

    gz = ExecuteProcess(
        cmd=["gz", "sim", "-r", "-s", "-v", "4", world_path],
        output="both"
    )

    # =========================
    # ROBOT DESCRIPTION
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

            "EE": "true",
            "EE_name": "robotiq_2f85",
        },
    ).toxml()

    print("ROBOT DESCRIPTION LENGTH:", len(robot_description_content))

    robot_description = {"robot_description": robot_description_content}

    # =========================
    # MOVEIT CONFIG
    # =========================

    robot_description_semantic = {
        "robot_description_semantic": load_file(
            "ros2srrc_ur5_moveit2",
            "config/ur5robotiq_2f85.srdf"
        )
    }

    kinematics_yaml = load_yaml(
        "ur5_gripper_moveit_config",
        "config/kinematics.yaml"
    )

    moveit_controllers = {
        "moveit_simple_controller_manager": load_yaml(
            "ur5_gripper_moveit_config",
            "config/moveit_controllers.yaml"
        )
    }

    # =========================
    # CORE NODES
    # =========================

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-param", "robot_description",
            "-name", "ur5",
            "-x", "0.0",
            "-y", "0.0",
            "-z", "0.9",
        ],
        parameters=[robot_description],
        output="both",
    )

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
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
        ],
    )

    joint_trajectory_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_trajectory_controller",
            "--controller-manager",
            "/controller_manager",
        ],
    )

    gripper_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "gripper_controller",
            "--controller-manager",
            "/controller_manager",
        ],
    )

    delayed_joint_state_broadcaster = TimerAction(
        period=8.0,
        actions=[joint_state_broadcaster],
    )

    # =========================
    # MOVEIT
    # =========================

    move_group = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="both",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            moveit_controllers,
            {"moveit_controller_manager": "moveit_simple_controller_manager/MoveItSimpleControllerManager"},
            {"use_sim_time": True},
        ],
    )

    # =========================
    # EXECUTION NODES
    # =========================

    common_params = [
        robot_description,
        robot_description_semantic,
        kinematics_yaml,
        {"use_sim_time": True},
        {"ROB_PARAM": "ur5"},
        {"EE_PARAM": "robotiq_2f85"},
    ]

    move_node = Node(
        name="move",
        package="ros2srrc_execution",
        executable="move",
        output="screen",
        arguments=['--ros-args', '--log-level', 'debug'],
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            moveit_controllers,
            {"moveit_controller_manager": "moveit_simple_controller_manager/MoveItSimpleControllerManager"},
            {"use_sim_time": True},
            {"ROB_PARAM": "ur5"},
            {"EE_PARAM": "robotiq_2f85"},
        ],
    )

    robmove_node = Node(
        name="robmove",
        package="ros2srrc_execution",
        executable="robmove",
        output="both",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            moveit_controllers,
            {"moveit_controller_manager": "moveit_simple_controller_manager/MoveItSimpleControllerManager"},
            {"use_sim_time": True},
            {"ROB_PARAM": "ur5"},
            {"EE_PARAM": "robotiq_2f85"},
            {"ENV_PARAM": "gazebo"},
        ],
    )

    robpose_node = Node(
        name="robpose",
        package="ros2srrc_execution",
        executable="robpose",
        output="both",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            moveit_controllers,
            {"moveit_controller_manager": "moveit_simple_controller_manager/MoveItSimpleControllerManager"},
            {"use_sim_time": True},
            {"ROB_PARAM": "ur5"},
            {"EE_PARAM": "robotiq_2f85"},
            {"ENV_PARAM": "gazebo"},
        ],
    )

    delayed_spawn = TimerAction(
        period=5.0,
        actions=[spawn_robot],
    )

    delayed_execution_nodes = TimerAction(
        period=10.0,
        actions=[
            ExecuteProcess(cmd=["echo", ">>> LAUNCH: intentando lanzar move_node"]),
            move_node,
            robmove_node,
            robpose_node
        ],
    )

    print(">>> LAUNCH: move_node configurado")

    return LaunchDescription([

        gz,
        robot_state_publisher,
        clock_bridge,
        delayed_spawn,
        delayed_joint_state_broadcaster,
        delayed_execution_nodes,

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
                target_action=gripper_controller,
                on_exit=[
                    TimerAction(
                        period=2.0,
                        actions=[move_group],
                    )
                ],
            )
        ),
    ])