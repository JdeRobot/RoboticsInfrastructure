"""
Pick Place Harmonic - RViz + MoveIt Launcher
Launches ONLY: MoveIt move_group + RViz with motion planning
Assumes Gazebo and robot are already running
"""

import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import TimerAction
from ament_index_python.packages import get_package_share_directory
import xacro


def generate_launch_description():
    # Get package directories
    pkg_share_dir = get_package_share_directory("custom_robots")
    moveit_config_package = "ur5_gripper_moveit_config"
    moveit_pkg_share = get_package_share_directory(moveit_config_package)

    # Robot description (must match what's in Gazebo)
    xacro_file = os.path.join(pkg_share_dir, "models/ur5", "ur5.urdf.xacro")
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

    # SRDF
    srdf_file = os.path.join(moveit_pkg_share, "srdf", "ur5_robotiq.srdf")
    with open(srdf_file, "r") as file:
        robot_description_semantic = {"robot_description_semantic": file.read()}

    # Kinematics
    kinematics_yaml = os.path.join(moveit_pkg_share, "config", "kinematics.yaml")

    # OMPL planning
    ompl_planning_yaml = os.path.join(moveit_pkg_share, "config", "ompl_planning.yaml")

    # MoveIt controllers
    moveit_controllers = os.path.join(moveit_pkg_share, "config", "controllers.yaml")

    # Planning pipeline
    planning_pipelines_config = {
        "planning_pipelines": ["ompl"],
        "default_planning_pipeline": "ompl",
        "ompl": {
            "planning_plugin": "ompl_interface/OMPLPlanner",
            "request_adapters": "default_planner_request_adapters/AddTimeOptimalParameterization default_planner_request_adapters/ResolveConstraintFrames default_planner_request_adapters/FixWorkspaceBounds default_planner_request_adapters/FixStartStateBounds default_planner_request_adapters/FixStartStateCollision default_planner_request_adapters/FixStartStatePathConstraints",
            "start_state_max_bounds_error": 0.1,
        },
    }

    # Trajectory execution
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

    # MoveIt move_group node

    # RViz with MoveIt configuration
    rviz_config_file = os.path.join(moveit_pkg_share, "rviz", "moveit.rviz")

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

    # Delay RViz after MoveIt
    delay_rviz = TimerAction(
        period=3.0,
        actions=[rviz_node],
    )

    return LaunchDescription(
        [
            delay_rviz,
        ]
    )
