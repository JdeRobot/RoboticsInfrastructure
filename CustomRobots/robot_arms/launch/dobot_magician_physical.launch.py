from launch.actions import (
    DeclareLaunchArgument,
    OpaqueFunction,
)
from launch.substitutions import LaunchConfiguration
from launch import LaunchDescription
from launch_ros.actions import Node

import os
import xacro
import yaml
from ament_index_python.packages import get_package_share_directory


def load_file(package_name, file_path):
    pkg_path = get_package_share_directory(package_name)
    with open(os.path.join(pkg_path, file_path), "r") as f:
        return f.read()


def load_yaml(package_name, file_path):
    pkg_path = get_package_share_directory(package_name)
    with open(os.path.join(pkg_path, file_path), "r") as f:
        return yaml.safe_load(f)


def launch_setup(context):
    x = LaunchConfiguration("x")
    y = LaunchConfiguration("y")
    z = LaunchConfiguration("z")
    R = LaunchConfiguration("R")
    P = LaunchConfiguration("P")
    Y = LaunchConfiguration("Y")
    end_effector = LaunchConfiguration("end_effector").perform(context)
    has_gripper = end_effector == "gripper"

    package_dir = get_package_share_directory("custom_robots")

    # Same MoveIt stack as the simulated arm with the bridge in place of Gazebo
    robot_description_content = xacro.process_file(
        os.path.join(
            package_dir, "models", "dobot_magician", "dobot_magician.urdf.xacro"
        ),
        mappings={
            "name": "dobot_magician",
            "prefix": "",
            "use_fake_hardware": "false",
            "sim_gazebo": "false",
            "sim_gz": "false",
            "end_effector": end_effector,
        },
    ).toxml()
    robot_description = {"robot_description": robot_description_content}

    robot_description_semantic = {
        "robot_description_semantic": load_file(
            "ros2srrc_dobot_magician_moveit2",
            f"config/dobot_magician_{end_effector}.srdf",
        )
    }

    kinematics_yaml = load_yaml(
        "dobot_magician_gripper_moveit_config", "config/kinematics.yaml"
    )
    kinematics_yaml = {
        "robot_description_kinematics": kinematics_yaml["/**"]["ros__parameters"]
    }

    moveit_controllers = load_yaml(
        "dobot_magician_gripper_moveit_config",
        "config/moveit_controllers.yaml"
        if has_gripper
        else f"config/moveit_controllers_{end_effector}.yaml",
    )["/**"]["ros__parameters"]

    ompl_planning = load_yaml(
        "dobot_magician_gripper_moveit_config", "config/ompl_planning.yaml"
    )["/**"]["ros__parameters"]

    planning_pipelines_config = {
        "planning_pipelines": ["ompl", "pilz_industrial_motion_planner"],
        "default_planning_pipeline": "pilz_industrial_motion_planner",
        "ompl": {
            "planning_plugin": "ompl_interface/OMPLPlanner",
        },
        "pilz_industrial_motion_planner": {
            "planning_plugin": "pilz_industrial_motion_planner/CommandPlanner",
            "request_adapters": "",
            "start_state_max_bounds_error": 0.1,
            "default_planner_config": "PTP",
        },
    }

    move_group_capabilities = {
        "capabilities": "pilz_industrial_motion_planner/MoveGroupSequenceAction "
        "pilz_industrial_motion_planner/MoveGroupSequenceService"
    }

    combined_planning = {
        "robot_description_planning": {
            **load_yaml("ros2srrc_robots", "dobot_magician/config/joint_limits.yaml"),
            **load_yaml(
                "ros2srrc_robots", "dobot_magician/config/pilz_cartesian_limits.yaml"
            ),
        }
    }

    # The real arm can lag behind the planned timing so MoveIt must not cancel slow moves
    trajectory_execution = {
        "trajectory_execution.execution_duration_monitoring": False,
    }

    moveit_common = [
        robot_description,
        robot_description_semantic,
        kinematics_yaml,
        ompl_planning,
        {"use_sim_time": False},
        {"ROB_PARAM": "dobot_magician"},
        {"ROB_GROUP": "dobot_magician_arm"},
    ]
    controller_manager = {
        "moveit_controller_manager": "moveit_simple_controller_manager/MoveItSimpleControllerManager"
    }

    move = Node(
        package="ros2srrc_execution",
        executable="move",
        name="move_action_server",
        output="screen",
        parameters=moveit_common
        + [
            moveit_controllers,
            controller_manager,
            {"EE_PARAM": "dobot_gripper" if has_gripper else "none"},
        ],
    )

    robmove = Node(
        package="ros2srrc_execution",
        executable="robmove",
        name="Robmove",
        output="screen",
        parameters=moveit_common + [moveit_controllers, controller_manager],
    )

    robpose = Node(
        package="ros2srrc_execution",
        executable="robpose",
        name="robpose",
        output="screen",
        parameters=moveit_common,
    )

    move_group = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            planning_pipelines_config,
            move_group_capabilities,
            moveit_controllers,
            combined_planning,
            trajectory_execution,
            {"use_sim_time": False},
        ],
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[robot_description, {"use_sim_time": False}],
        output="screen",
    )

    static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=[x, y, z, R, P, Y, "world", "base_link"],
    )

    bridge = Node(
        package="dobot_magician_bridge",
        executable="bridge_node",
        output="screen",
        parameters=[
            {
                "port": LaunchConfiguration("port"),
                "end_effector": end_effector,
            }
        ],
    )

    return [
        bridge,
        robot_state_publisher,
        static_tf,
        move_group,
        move,
        robmove,
        robpose,
    ]


def generate_launch_description():
    declared_arguments = [
        # The pose only places the robot in RViz
        DeclareLaunchArgument("x", default_value="0"),
        DeclareLaunchArgument("y", default_value="0"),
        DeclareLaunchArgument("z", default_value="0.131305"),
        DeclareLaunchArgument("R", default_value="0"),
        DeclareLaunchArgument("P", default_value="0"),
        DeclareLaunchArgument("Y", default_value="0"),
        DeclareLaunchArgument("entity", default_value="dobot_magician_suction_cup"),
        DeclareLaunchArgument("end_effector", default_value="suction_cup"),
        # auto finds the Dobot by its USB ids
        DeclareLaunchArgument("port", default_value="auto"),
    ]

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
