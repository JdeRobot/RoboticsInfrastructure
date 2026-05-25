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


def generate_launch_description():

    # =========================
    # ROBOT DESCRIPTION (URDF)
    # =========================
    xacro_file = os.path.join(
        get_package_share_directory("ros2srrc_ur5_gazebo"),
        "urdf",
        "ur5_robotiq_2f85_with_cams.urdf.xacro",
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

    robot_description = {"robot_description": robot_description_content}

    # =========================
    # SRDF (SEMANTIC)
    # =========================
    robot_description_semantic = {
        "robot_description_semantic": load_file(
            "ros2srrc_ur5_moveit2", "config/ur5robotiq_2f85.srdf"
        )
    }

    # =========================
    # KINEMATICS
    # =========================
    kinematics_yaml = load_yaml("ur5_gripper_moveit_config", "config/kinematics.yaml")

    kinematics_yaml = {
        "robot_description_kinematics": kinematics_yaml["/**"]["ros__parameters"]
    }

    # =========================
    # CONTROLLERS (MoveIt)
    # =========================
    moveit_controllers = load_yaml(
        "ur5_gripper_moveit_config", "config/moveit_controllers.yaml"
    )

    ompl_planning = load_yaml("ur5_gripper_moveit_config", "config/ompl_planning.yaml")

    ompl_planning = ompl_planning["/**"]["ros__parameters"]

    moveit_controllers = moveit_controllers["/**"]["ros__parameters"]

    # =========================
    # NODOS
    # =========================

    move = Node(
        package="ros2srrc_execution",
        executable="move",
        name="move_action_server",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            moveit_controllers,
            ompl_planning,
            {
                "moveit_controller_manager": "moveit_simple_controller_manager/MoveItSimpleControllerManager"
            },
            {"use_sim_time": True},
            {"ROB_PARAM": "ur5"},
            {"EE_PARAM": "robotiq_2f85"},
        ],
    )

    robmove = Node(
        package="ros2srrc_execution",
        executable="robmove",
        name="Robmove",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            moveit_controllers,
            ompl_planning,
            {
                "moveit_controller_manager": "moveit_simple_controller_manager/MoveItSimpleControllerManager"
            },
            {"use_sim_time": True},
            {"ROB_PARAM": "ur5"},
        ],
    )

    robpose = Node(
        package="ros2srrc_execution",
        executable="robpose",
        name="robpose",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            ompl_planning,
            {"use_sim_time": True},
            {"ROB_PARAM": "ur5"},
        ],
    )

    # =========================
    # LAUNCH
    # =========================

    return LaunchDescription([move, robmove, robpose])
