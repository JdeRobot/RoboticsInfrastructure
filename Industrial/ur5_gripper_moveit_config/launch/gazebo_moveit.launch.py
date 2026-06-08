#!/usr/bin/env python3
"""
Combined launch file for UR5 + Robotiq Gripper in Gazebo Sim with MoveIt2
Launches Gazebo, spawns robot, and starts MoveIt move_group
"""

import os
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    RegisterEventHandler,
    TimerAction,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
import xacro


def generate_launch_description():
    # Get workspace directory from package share
    pkg_share_dir = get_package_share_directory("ur5_gripper_description")
    workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(pkg_share_dir)))

    # Prepare environment variables for Gazebo
    gz_lib_path = os.path.join(workspace_dir, "gz_ros2_control", "lib")
    ur_share = os.path.join(workspace_dir, "ur5_gripper_description", "share")
    robotiq_share = os.path.join(workspace_dir, "robotiq_description", "share")

    gz_env = {
        "GZ_SIM_RESOURCE_PATH": f"{ur_share}:{robotiq_share}:{os.environ.get('GZ_SIM_RESOURCE_PATH', '')}",
        "GZ_SIM_SYSTEM_PLUGIN_PATH": f"{gz_lib_path}:{os.environ.get('GZ_SIM_SYSTEM_PLUGIN_PATH', '')}",
        "LD_LIBRARY_PATH": f"{gz_lib_path}:{os.environ.get('LD_LIBRARY_PATH', '')}",
    }

    # Declare arguments
    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "ur_type",
            default_value="ur5",
            description="Type/series of UR robot.",
        )
    )

    # Get URDF via xacro
    xacro_file = os.path.join(
        get_package_share_directory("ur5_gripper_description"),
        "urdf",
        "ur5_robotiq85_gripper.urdf.xacro",
    )

    controllers_file = os.path.join(
        get_package_share_directory("ur5_gripper_description"),
        "config",
        "ur5_controllers.yaml",
    )

    # Process xacro
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

    # Robot state publisher
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    # Gazebo Sim (Harmonic) - with environment variables
    gz_cmd = (
        f'export GZ_SIM_SYSTEM_PLUGIN_PATH="{gz_env["GZ_SIM_SYSTEM_PLUGIN_PATH"]}" && '
        f'export GZ_SIM_RESOURCE_PATH="{gz_env["GZ_SIM_RESOURCE_PATH"]}" && '
        f'export LD_LIBRARY_PATH="{gz_env["LD_LIBRARY_PATH"]}" && '
        "gz sim -r -v 4 empty.sdf"
    )

    gazebo = ExecuteProcess(cmd=["bash", "-c", gz_cmd], output="screen", shell=False)

    # Spawn robot
    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic",
            "robot_description",
            "-name",
            "ur5_robotiq",
            "-allow_renaming",
            "true",
        ],
        output="screen",
    )

    # Bridge for clock
    gz_ros2_bridge_clock = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    # Load joint state broadcaster
    load_joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
        ],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    # Load arm controller
    load_joint_trajectory_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_trajectory_controller", "-c", "/controller_manager"],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    # Load gripper controller
    load_gripper_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gripper_controller", "-c", "/controller_manager"],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    # MoveIt configuration
    moveit_config_package = "ur5_gripper_moveit_config"

    # Load MoveIt parameters
    ompl_planning_yaml = os.path.join(
        get_package_share_directory(moveit_config_package),
        "config",
        "ompl_planning.yaml",
    )

    kinematics_yaml = os.path.join(
        get_package_share_directory(moveit_config_package),
        "config",
        "kinematics.yaml",
    )

    # SRDF
    srdf_file = os.path.join(
        get_package_share_directory(moveit_config_package),
        "srdf",
        "ur5_robotiq.srdf",
    )

    with open(srdf_file, "r") as file:
        robot_description_semantic = {"robot_description_semantic": file.read()}

    # MoveIt controllers
    moveit_controllers = os.path.join(
        get_package_share_directory(moveit_config_package),
        "config",
        "controllers.yaml",
    )

    # Trajectory execution parameters
    trajectory_execution = {
        "moveit_manage_controllers": True,
        "trajectory_execution.allowed_execution_duration_scaling": 1.2,
        "trajectory_execution.allowed_goal_duration_margin": 0.5,
        "trajectory_execution.allowed_start_tolerance": 0.01,
    }

    planning_scene_monitor_parameters = {
        "publish_planning_scene": True,
        "publish_geometry_updates": True,
        "publish_state_updates": True,
        "publish_transforms_updates": True,
    }

    # Planning pipeline configuration - only use OMPL, disable CHOMP
    planning_pipelines_config = {
        "planning_pipelines": ["ompl"],
        "default_planning_pipeline": "ompl",
        "ompl": {
            "planning_plugin": "ompl_interface/OMPLPlanner",
            "request_adapters": "default_planner_request_adapters/AddTimeOptimalParameterization default_planner_request_adapters/ResolveConstraintFrames default_planner_request_adapters/FixWorkspaceBounds default_planner_request_adapters/FixStartStateBounds default_planner_request_adapters/FixStartStateCollision default_planner_request_adapters/FixStartStatePathConstraints",
            "start_state_max_bounds_error": 0.1,
        },
    }

    # MoveIt move_group node
    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            ompl_planning_yaml,
            planning_pipelines_config,
            trajectory_execution,
            moveit_controllers,
            planning_scene_monitor_parameters,
            {"use_sim_time": True},
        ],
        arguments=["--ros-args", "--log-level", "moveit_robot_model:=FATAL"],
    )

    # RViz with MoveIt configuration
    rviz_config_file = os.path.join(
        get_package_share_directory(moveit_config_package),
        "rviz",
        "moveit.rviz",
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        parameters=[
            robot_description,
            robot_description_semantic,
            ompl_planning_yaml,
            kinematics_yaml,
            {"use_sim_time": True},
        ],
    )

    # Delay controller spawning after robot spawn
    delay_joint_state_broadcaster = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[load_joint_state_broadcaster],
        )
    )

    delay_joint_trajectory_controller = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=load_joint_state_broadcaster,
            on_exit=[load_joint_trajectory_controller],
        )
    )

    delay_gripper_controller = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=load_joint_trajectory_controller,
            on_exit=[load_gripper_controller],
        )
    )

    # Delay MoveIt after controllers are loaded
    delay_move_group = TimerAction(
        period=5.0,
        actions=[move_group_node],
    )

    delay_rviz = TimerAction(
        period=7.0,
        actions=[rviz_node],
    )

    nodes = [
        gazebo,
        robot_state_publisher,
        spawn_entity,
        gz_ros2_bridge_clock,
        delay_joint_state_broadcaster,
        delay_joint_trajectory_controller,
        delay_gripper_controller,
        delay_move_group,
        delay_rviz,
    ]

    return LaunchDescription(declared_arguments + nodes)
