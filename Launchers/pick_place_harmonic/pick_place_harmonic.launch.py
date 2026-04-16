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
from launch.actions import LogInfo
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

debug_args = ["--ros-args", "--log-level", "info"]

def debug_event(name, action):
    return RegisterEventHandler(
        OnProcessStart(
            target_action=action,
            on_start=[LogInfo(msg=f"STARTED: {name}")]
        )
    )

def debug_exit(name, action):
    return RegisterEventHandler(
        OnProcessExit(
            target_action=action,
            on_exit=[LogInfo(msg=f"EXIT: {name}")]
        )
    )


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

    resource_path = (
        os.path.dirname(get_package_share_directory("ur5_gripper_description")) + ":" +
        os.path.dirname(get_package_share_directory("robotiq_description")) + ":" +
        os.path.join(
            get_package_share_directory("robotiq_description"),
            "world",
            "models"
        )
    )

    set_resource_path = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=resource_path
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
        output="both",
        additional_env={
            "GZ_SIM_SYSTEM_PLUGIN_PATH": gz_plugin_path,
            "LD_LIBRARY_PATH": gz_plugin_path + ":/usr/lib/x86_64-linux-gnu:" + existing_ld,
            "GZ_SIM_RESOURCE_PATH": resource_path,
        }
    )

    # =========================
    # ROBOT DESCRIPTION
    # =========================

    xacro_file = os.path.join(
        get_package_share_directory("ur5_gripper_description"),
        "urdf",
        "ur5_robotiq85_gripper.urdf.xacro"
    )

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

    ompl_planning_yaml = load_yaml(
        "ur5_gripper_moveit_config",
        "config/ompl_planning.yaml"
    )

    ompl_planning_yaml = ompl_planning_yaml["/**"]["ros__parameters"]

    planning_pipelines_config = {
        "planning_pipelines": ["ompl"],
        "default_planning_pipeline": "ompl",
    }

    trajectory_execution = {
        "moveit_manage_controllers": True,
    }

    planning_scene_monitor_parameters = {
        "publish_planning_scene": True,
        "publish_geometry_updates": True,
        "publish_state_updates": True,
        "publish_transforms_updates": True,
    }

    # =========================
    # CORE NODES
    # =========================

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        emulate_tty=True,
        parameters=[robot_description, {"use_sim_time": True}],
    )

    static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=[
            "0", "0", "0.9", "0", "0", "0", "world", "base_link"
        ],
        output="screen",
        emulate_tty=True,
        parameters=[{"use_sim_time": True}],
    )

    spawn_robot = Node(
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
        ] + debug_args,
        output="screen",
        emulate_tty=True,
    )

    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock]"
        ],
        output="screen",
        emulate_tty=True,
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
        ] + debug_args,
        output="screen",
        emulate_tty=True,
    )

    joint_trajectory_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_trajectory_controller",
            "--controller-manager",
            "/controller_manager",
        ] + debug_args,
        output="screen",
        emulate_tty=True,
    )

    gripper_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "gripper_controller",
            "--controller-manager",
            "/controller_manager",
        ] + debug_args,
        output="screen",
        emulate_tty=True,
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
        output="screen",
        emulate_tty=True,
        arguments=debug_args,
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            ompl_planning_yaml,
            planning_pipelines_config,
            trajectory_execution,
            planning_scene_monitor_parameters,
            moveit_controllers,
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

    move_action_server = Node(
        name="move_action_server",
        package="ros2srrc_execution",
        executable="move",
        output="screen",
        emulate_tty=True,
        arguments=["--ros-args", "--log-level", "warn"],
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
        name="Robmove",
        package="ros2srrc_execution",
        executable="robmove",
        output="screen",
        emulate_tty=True,
        arguments=debug_args,
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
        output="screen",
        emulate_tty=True,
        arguments=debug_args,
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


    print(">>> LAUNCH: move_node configurado")


    return LaunchDescription([
        SetEnvironmentVariable(name="RCUTILS_LOGGING_BUFFERED_STREAM", value="1"),
        SetEnvironmentVariable(name="RCUTILS_COLORIZED_OUTPUT", value="1"),
        SetParameter(name="use_sim_time", value=True),

        set_gz_plugin_path,
        set_ld_library_path,
        set_resource_path, 

        ExecuteProcess(cmd=["echo", "===== START GAZEBO ====="]),
        gz,

        ExecuteProcess(cmd=["echo", "===== START CORE NODES ====="]),
        clock_bridge,
        robot_state_publisher,
        static_tf,

        ExecuteProcess(cmd=["echo", "===== SPAWN ROBOT ====="]),
        spawn_robot,

        ExecuteProcess(cmd=["echo", "===== LOAD CONTROLLERS ====="]),

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

        ExecuteProcess(cmd=["echo", "===== START MOVE GROUP ====="]),

        RegisterEventHandler(
            OnProcessExit(
                target_action=gripper_controller,
                on_exit=[
                    move_group,

                    TimerAction(
                        period=3.0,
                        actions=[
                            move_action_server,
                            robmove_node,
                            robpose_node
                        ],
                    ),
                ],
            )
        ),


        debug_event("gz", gz),
        debug_event("robot_state_publisher", robot_state_publisher),
        debug_event("spawn_robot", spawn_robot),
        debug_event("joint_state_broadcaster", joint_state_broadcaster),
        debug_event("joint_trajectory_controller", joint_trajectory_controller),
        debug_event("gripper_controller", gripper_controller),
        debug_event("move_group", move_group),
        debug_event("move_action_server", move_action_server),
        debug_event("robmove", robmove_node),
        debug_event("robpose", robpose_node),

        debug_exit("gz", gz),
        debug_exit("move_group", move_group),
        debug_exit("move_action_server", move_action_server),
        debug_exit("robmove", robmove_node),
        debug_exit("robpose", robpose_node),

    ])