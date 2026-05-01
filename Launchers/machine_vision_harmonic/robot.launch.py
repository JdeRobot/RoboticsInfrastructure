#!/usr/bin/env python3

import os
import xacro
import yaml

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit
from ament_index_python.packages import get_package_share_directory


def load_file(package_name, file_path):
    pkg_path = get_package_share_directory(package_name)
    with open(os.path.join(pkg_path, file_path), "r") as f:
        return f.read()


def load_yaml(package_name, file_path):
    pkg_path = get_package_share_directory(package_name)
    with open(os.path.join(pkg_path, file_path), "r") as f:
        return yaml.safe_load(f)


def generate_launch_description():

    # =========================
    # PATHS
    # =========================

    pkg_desc = get_package_share_directory("ur5_gripper_description")
    pkg_gazebo = get_package_share_directory("ros2srrc_ur5_gazebo")

    xacro_file = os.path.join(
        pkg_gazebo,
        "urdf",
        "ur5_robotiq_2f85_with_cams_gz.urdf.xacro"
    )

    controllers_file = os.path.join(
        pkg_desc,
        "config",
        "ur5_controllers.yaml"
    )

    # =========================
    # ROBOT DESCRIPTION
    # =========================

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
            "hmi": "false",
            "EE": "true",
            "EE_name": "robotiq_2f85",
        },
    ).toxml()

    robot_description = {"robot_description": robot_description_content}

    # =========================
    # MOVEIT CONFIG
    # =========================

    robot_description_semantic = {
        "robot_description_semantic": load_file(
            "ros2srrc_ur5_moveit2", "config/ur5robotiq_2f85.srdf"
        )
    }

    kinematics_yaml = load_yaml(
        "ur5_gripper_moveit_config", "config/kinematics.yaml"
    )
    kinematics_yaml = {
        "robot_description_kinematics": kinematics_yaml["/**"]["ros__parameters"]
    }

    moveit_controllers = load_yaml(
        "ur5_gripper_moveit_config", "config/moveit_controllers.yaml"
    )
    moveit_controllers = moveit_controllers["/**"]["ros__parameters"]

    planning_pipelines_config = {
        "planning_pipelines": ["ompl", "pilz_industrial_motion_planner"],
        "default_planning_pipeline": "pilz_industrial_motion_planner",
        "ompl": {"planning_plugin": "ompl_interface/OMPLPlanner"},
        "pilz_industrial_motion_planner": {
            "planning_plugin": "pilz_industrial_motion_planner/CommandPlanner",
            "request_adapters": "",
            "start_state_max_bounds_error": 0.1,
            "default_planner_config": "PTP",
        },
    }

    pilz_cartesian_limits = load_yaml(
        "ros2srrc_robots", "ur5/config/pilz_cartesian_limits.yaml"
    )

    joint_limits_yaml = load_yaml(
        "ros2srrc_robots", "ur5/config/joint_limits.yaml"
    )

    combined_planning = {
        "robot_description_planning": {
            **joint_limits_yaml,
            **pilz_cartesian_limits,
        }
    }

    # =========================
    # CORE NODES
    # =========================

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[robot_description, {"use_sim_time": True}],
        output="screen",
    )

    static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0", "0", "0.9", "0", "0", "0", "world", "base_link"],
    )

    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name", "ur5",
            "-topic", "robot_description",
            "-x", "0.0",
            "-y", "0.0",
            "-z", "0.9",
        ],
        output="screen",
    )

    # =========================
    # BRIDGES
    # =========================

    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock]"],
        parameters=[{"use_sim_time": True}],
        output="screen",
    )

    camera_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/hand_camera/image@sensor_msgs/msg/Image@gz.msgs.Image",
            "/hand_camera/depth_image@sensor_msgs/msg/Image@gz.msgs.Image",
            "/base_camera/image@sensor_msgs/msg/Image@gz.msgs.Image",
            "/base_camera/depth_image@sensor_msgs/msg/Image@gz.msgs.Image",
        ],
        output="screen",
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

    delay_controllers = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_entity,
            on_exit=[
                joint_state_broadcaster,
                joint_trajectory_controller,
                gripper_controller,
            ],
        )
    )

    # =========================
    # MOVEIT
    # =========================

    move_group = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            planning_pipelines_config,
            moveit_controllers,
            combined_planning,
            {"use_sim_time": True},
        ],
    )

    # =========================
    # LAUNCH
    # =========================

    return LaunchDescription([
        clock_bridge,
        camera_bridge,
        robot_state_publisher,
        static_tf,
        spawn_entity,
        delay_controllers,
        move_group,
    ])