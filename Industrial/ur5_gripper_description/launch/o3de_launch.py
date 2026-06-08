#!/usr/bin/env python3
# Launch file for spawning UR5 with Robotiq gripper in Gazebo Sim (Harmonic)

import os
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    RegisterEventHandler,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.conditions import IfCondition
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
    # Go up from install/ur5_gripper_description/share/ur5_gripper_description to install/
    workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(pkg_share_dir)))

    # Prepare environment variables for Gazebo
    ur_share = os.path.join(workspace_dir, "ur5_gripper_description", "share")
    robotiq_share = os.path.join(workspace_dir, "robotiq_description", "share")

    # Declare arguments
    declared_arguments = [
        DeclareLaunchArgument("ur_type", default_value="ur5"),
        DeclareLaunchArgument("launch_rviz", default_value="true"),
    ]

    # Initialize Arguments
    ur_type = LaunchConfiguration("ur_type")
    prefix = LaunchConfiguration("prefix")
    launch_rviz = LaunchConfiguration("launch_rviz")

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

    # Process xacro directly to avoid Command() stderr issues
    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "ur_type": "ur5",
            "name": "ur",
            "prefix": "",
            "use_fake_hardware": "false",
            "simulation_controllers": controllers_file,
        },
    ).toxml()

    robot_description = {"robot_description": robot_description_content}

    # Node for robot state publisher
    node_robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": True}],
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

    # MoveIt
    moveit_config_package = "ur5_gripper_moveit_config"
    moveit_pkg = get_package_share_directory(moveit_config_package)
    
    ompl_planning_yaml = os.path.join(moveit_pkg, "config", "ompl_planning.yaml")
    kinematics_yaml = os.path.join(moveit_pkg, "config", "kinematics_o3de.yaml")
    srdf_file = os.path.join(moveit_pkg, "srdf", "ur5_robotiq.srdf")
    moveit_controllers = os.path.join(moveit_pkg, "config", "controllers.yaml")
    
    with open(srdf_file, "r") as f:
        robot_description_semantic = {"robot_description_semantic": f.read()}
        
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

    planning_pipelines_config = {
        "planning_pipelines": ["ompl"],
        "default_planning_pipeline": "ompl",
        "ompl": {
            "planning_plugin": "ompl_interface/OMPLPlanner",
            "request_adapters": "default_planner_request_adapters/AddTimeOptimalParameterization default_planner_request_adapters/ResolveConstraintFrames default_planner_request_adapters/FixWorkspaceBounds default_planner_request_adapters/FixStartStateBounds default_planner_request_adapters/FixStartStateCollision default_planner_request_adapters/FixStartStatePathConstraints",
            "start_state_max_bounds_error": 0.1,
        },
    }
    
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
        condition=IfCondition(LaunchConfiguration("launch_rviz")),
    )

    
    # RViz
    rviz_config_file = PathJoinSubstitution(
        [FindPackageShare("ur5_gripper_description"), "rviz", "moveit.rviz"]
    )

    rviz_config_file = os.path.join(moveit_pkg, "rviz", "moveit.rviz")
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
            {"use_sim_time": True}
        ],
        condition=IfCondition(LaunchConfiguration("launch_rviz")),
    )

    # Delays
    delay_mg = TimerAction(period=10.0, actions=[move_group_node])
    delay_rviz = TimerAction(period=12.0, actions=[rviz_node])
    
    nodes = [
        node_robot_state_publisher,
        #load_joint_state_broadcaster,
        #load_joint_trajectory_controller,
        #load_gripper_controller,
        delay_mg,
        delay_rviz,
    ]

    return LaunchDescription(declared_arguments + nodes)
