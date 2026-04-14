#!/usr/bin/env python3

import os
import xacro
import yaml

from launch import LaunchDescription
from launch.actions import ExecuteProcess, RegisterEventHandler, TimerAction
from launch.event_handlers import OnProcessExit, OnProcessStart
from launch_ros.actions import Node, SetParameter
from ament_index_python.packages import get_package_share_directory
from launch.actions import SetEnvironmentVariable


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

    # =========================
    # GAZEBO ENV PATHS (CLAVE)
    # =========================

    gz_ros2_control_path = "/home/ws/install/gz_ros2_control/lib"
    gz_link_attacher_path = "/home/ws/install/gz_link_attacher/lib"

    gz_plugin_path = (
        gz_link_attacher_path + ":" +
        gz_ros2_control_path + ":" +
        "/opt/ros/humble/lib"
    )

    print("DEBUG GZ_SIM_SYSTEM_PLUGIN_PATH =", gz_plugin_path)

    set_gz_plugin_path = SetEnvironmentVariable(
        name="GZ_SIM_SYSTEM_PLUGIN_PATH",
        value=gz_plugin_path
    )

    existing_ld = os.environ.get("LD_LIBRARY_PATH", "")

    set_ld_library_path = SetEnvironmentVariable(
        name="LD_LIBRARY_PATH",
        value=gz_plugin_path + ":/usr/lib/x86_64-linux-gnu:" + existing_ld
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

    kinematics_yaml = {
        "robot_description_kinematics":
            kinematics_yaml["/**"]["ros__parameters"]
    }

    moveit_controllers = load_yaml(
        "ur5_gripper_moveit_config",
        "config/moveit_controllers.yaml"
    )

    moveit_controllers = moveit_controllers["/**"]["ros__parameters"]

    # =========================
    # CORE NODES
    # =========================

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0", "0", "0.9", "0", "0", "0", "world", "base_link"],
        output="both",
        parameters=[{"use_sim_time": True}],
    )

    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic", "robot_description",
            "-name", "ur5",
            "-allow_renaming", "true",
            "-x", "0.0",
            "-y", "0.0",
            "-z", "0.9",
            "-R", "0.0",
            "-P", "0.0",
            "-Y", "0.0",
        ],
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

    """delayed_joint_state_broadcaster = TimerAction(
        period=8.0,
        actions=[joint_state_broadcaster],
    )"""

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
            {"publish_robot_description_semantic": True},
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

    move_action_server = Node(
        name="move_action_server",
        package="ros2srrc_execution",
        executable="move",
        output="screen",
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

    """delayed_execution_nodes = TimerAction(
        period=10.0,
        actions=[
            ExecuteProcess(cmd=["echo", ">>> LAUNCH: intentando lanzar move_node"]),
            move_node,
            robmove_node,
            robpose_node
        ],
    )"""

    print(">>> LAUNCH: move_node configurado")

    """return LaunchDescription([
        SetParameter(name="use_sim_time", value=True),
        
        set_gz_plugin_path,
        set_ld_library_path,
        gz,
        robot_state_publisher,
        static_tf,
        clock_bridge,
        delayed_spawn,
        #delayed_joint_state_broadcaster,
        #delayed_execution_nodes,

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
                target_action=gripper_controller,
                on_exit=[
                    TimerAction(
                        period=12.0,
                        actions=[move_group],
                    )
                ],
            )
        ),

        RegisterEventHandler(
            OnProcessStart(
                target_action=move_group,
                on_start=[
                    TimerAction(
                        period=15.0,
                        actions=[
                            ExecuteProcess(cmd=["echo", ">>> move_group listo, lanzando ejecución"]),
                            move_node,
                            robmove_node,
                            robpose_node
                        ],
                    )
                ],
            )
        ),
    ])"""

    return LaunchDescription([
        SetParameter(name="use_sim_time", value=True),

        set_gz_plugin_path,
        set_ld_library_path,
        gz,
        clock_bridge,
        robot_state_publisher,
        static_tf,

        TimerAction(period=5.0, actions=[spawn_robot]),

        TimerAction(period=8.0, actions=[joint_state_broadcaster]),
        TimerAction(period=10.0, actions=[joint_trajectory_controller]),
        TimerAction(period=12.0, actions=[gripper_controller]),

        TimerAction(period=18.0, actions=[move_group]),

        TimerAction(period=20.0, actions=[move_action_server]),

        TimerAction(period=22.0, actions=[robmove_node, robpose_node]),
    ])