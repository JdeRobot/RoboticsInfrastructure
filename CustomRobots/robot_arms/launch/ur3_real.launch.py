from launch import LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node

import os
import yaml
import xacro

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

    package_dir = get_package_share_directory("custom_robots")

    ########################################################
    # ROBOT DESCRIPTION
    ########################################################

    xacro_file = os.path.join(
        package_dir,
        "models",
        "ur3_real",
        "ur3_real.urdf.xacro",
    )

    controllers_file = os.path.join(
        package_dir,
        "config",
        "ur3_controllers.yaml",
    )

    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "ur_type": "ur3",
            "name": "ur",
            "prefix": "",
            "use_fake_hardware": "false",
            "sim_gazebo": "false",
            "sim_gz": "false",
            "simulation_controllers": controllers_file,
            "hmi": "false",
            "EE": "false",
            "camera": "false",
        },
    ).toxml()

    robot_description = {
        "robot_description": robot_description_content
    }

    ########################################################
    # SRDF
    ########################################################

    robot_description_semantic = {
        "robot_description_semantic": load_file(
            "ros2srrc_ur3_moveit2",
            "config/ur3.srdf",
        )
    }

    ########################################################
    # KINEMATICS
    ########################################################

    kinematics_yaml = load_yaml(
        "ur3_gripper_moveit_config",
        "config/real_robot/kinematics_real.yaml",
    )

    kinematics_yaml = {
        "robot_description_kinematics":
        kinematics_yaml["/**"]["ros__parameters"]
    }

    ########################################################
    # MOVEIT CONTROLLERS
    ########################################################

    moveit_controllers = load_yaml(
        "ur3_gripper_moveit_config",
        "config/real_robot/moveit_controllers_real.yaml",
    )

    moveit_controllers = moveit_controllers["/**"]["ros__parameters"]

    ########################################################
    # OMPL
    ########################################################

    ompl_planning = load_yaml(
        "ur3_gripper_moveit_config",
        "config/ompl_planning.yaml",
    )

    ompl_planning = ompl_planning["/**"]["ros__parameters"]

    ########################################################
    # PILZ
    ########################################################

    planning_pipelines_config = {
        "planning_pipelines": [
            "ompl",
            "pilz_industrial_motion_planner",
        ],
        "default_planning_pipeline":
            "pilz_industrial_motion_planner",
        "ompl": {
            "planning_plugin":
                "ompl_interface/OMPLPlanner",
        },
        "pilz_industrial_motion_planner": {
            "planning_plugin":
                "pilz_industrial_motion_planner/CommandPlanner",
            "request_adapters": "",
            "start_state_max_bounds_error": 0.1,
            "default_planner_config": "PTP",
        },
    }

    move_group_capabilities = {
        "capabilities":
        "pilz_industrial_motion_planner/MoveGroupSequenceAction "
        "pilz_industrial_motion_planner/MoveGroupSequenceService"
    }

    ########################################################
    # LIMITS
    ########################################################

    pilz_cartesian_limits = load_yaml(
        "ros2srrc_robots",
        "ur3/config/pilz_cartesian_limits.yaml",
    )

    joint_limits_yaml = load_yaml(
        "ros2srrc_robots",
        "ur3/config/joint_limits.yaml",
    )

    combined_planning = {
        "robot_description_planning":
        {
            **joint_limits_yaml,
            **pilz_cartesian_limits,
        }
    }

    ########################################################
    # MOVE GROUP
    ########################################################

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
            {
                "moveit_controller_manager":
                "moveit_simple_controller_manager/MoveItSimpleControllerManager"
            },
            {
                "use_sim_time": False
            },
        ],
    )

    ########################################################
    # MOVE ACTION SERVER
    ########################################################

    move = Node(
        package="ros2srrc_execution",
        executable="move",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            moveit_controllers,
            ompl_planning,
            {
                "moveit_controller_manager":
                "moveit_simple_controller_manager/MoveItSimpleControllerManager"
            },
            {
                "ROB_PARAM": "ur3"
            },
            {
                "EE_PARAM": "none"
            },
            {
                "ROB_GROUP": "ur3_arm"
            },
            {
                "use_sim_time": False
            },
        ],
    )

    ########################################################
    # ROBMOVE
    ########################################################

    robmove = Node(
        package="ros2srrc_execution",
        executable="robmove",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            moveit_controllers,
            ompl_planning,
            {
                "moveit_controller_manager":
                "moveit_simple_controller_manager/MoveItSimpleControllerManager"
            },
            {
                "ROB_PARAM": "ur3"
            },
            {
                "ROB_GROUP": "ur3_arm"
            },
            {
                "use_sim_time": False
            },
        ],
    )

    ########################################################
    # ROBPOSE
    ########################################################

    robpose = Node(
        package="ros2srrc_execution",
        executable="robpose",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            ompl_planning,
            {
                "ROB_PARAM": "ur3"
            },
            {
                "ROB_GROUP": "ur3_arm"
            },
            {
                "use_sim_time": False
            },
        ],
    )

    return [
        move_group,
        move,
        robmove,
        robpose,
    ]


def generate_launch_description():
    return LaunchDescription([
        OpaqueFunction(function=launch_setup)
    ])