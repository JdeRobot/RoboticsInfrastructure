"""
Palletizing Harmonic - RViz + MoveIt Launcher
Launches ONLY: MoveIt move_group + RViz with motion planning
Assumes Gazebo and robot are already running (suction gripper variant)
"""

import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import TimerAction
from ament_index_python.packages import get_package_share_directory
import xacro
import yaml


def generate_launch_description():
    pkg_share_dir = get_package_share_directory("custom_robots")

    # Robot description — suction gripper (must match the SDF spawned in Gazebo)
    xacro_file = os.path.join(pkg_share_dir, "models/ur10", "ur10_suction.urdf.xacro")
    controllers_file = os.path.join(pkg_share_dir, "config", "ur10_suction", "controllers.yaml")

    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "ur_type": "ur10",
            "name": "ur",
            "prefix": "",
            "use_fake_hardware": "false",
            "sim_gazebo": "false",
            "sim_gz": "true",
            "simulation_controllers": controllers_file,
        },
    ).toxml()

    robot_description = {"robot_description": robot_description_content}

    # SRDF — suction variant (no finger-gripper group)
    srdf_file = os.path.join(pkg_share_dir, "config", "ur10_suction", "robot.srdf")
    with open(srdf_file, "r") as f:
        robot_description_semantic = {"robot_description_semantic": f.read()}

    # Kinematics / planning configs — UR10 suction specific
    kinematics_yaml = os.path.join(
        pkg_share_dir, "config", "ur10_suction", "kinematics.yaml"
    )
    ompl_planning_yaml = os.path.join(
        pkg_share_dir, "config", "ur10_suction", "ompl_planning.yaml"
    )

    planning_pipelines_config = {
        "planning_pipelines": ["ompl"],
        "default_planning_pipeline": "ompl",
        "ompl": {
            "planning_plugin": "ompl_interface/OMPLPlanner",
            "request_adapters": "default_planner_request_adapters/AddTimeOptimalParameterization default_planner_request_adapters/ResolveConstraintFrames default_planner_request_adapters/FixWorkspaceBounds default_planner_request_adapters/FixStartStateBounds default_planner_request_adapters/FixStartStateCollision default_planner_request_adapters/FixStartStatePathConstraints",
            "start_state_max_bounds_error": 0.1,
        },
    }

    rviz_config_file = os.path.join(
        pkg_share_dir, "config", "ur10_suction", "moveit.rviz"
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

    delay_rviz = TimerAction(
        period=3.0,
        actions=[rviz_node],
    )

    return LaunchDescription([delay_rviz])
