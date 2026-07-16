from launch import LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node

import os
import yaml

from ament_index_python.packages import get_package_share_directory
from launch.substitutions import (
    Command,
    PathJoinSubstitution,
    LaunchConfiguration,
    FindExecutable,
)

from launch_ros.substitutions import FindPackageShare

from launch_ros.parameter_descriptions import ParameterValue
from launch.actions import DeclareLaunchArgument


def load_file(package_name, file_path):
    pkg_path = get_package_share_directory(package_name)
    with open(os.path.join(pkg_path, file_path), "r") as f:
        return f.read()


def load_yaml(package_name, file_path):
    pkg_path = get_package_share_directory(package_name)
    with open(os.path.join(pkg_path, file_path), "r") as f:
        return yaml.safe_load(f)


def launch_setup(context):
    ur_type = LaunchConfiguration("ur_type")
    robot_ip = LaunchConfiguration("robot_ip")

    description_package = LaunchConfiguration("description_package")
    description_file = LaunchConfiguration("description_file")

    kinematics_params_file = LaunchConfiguration("kinematics_params_file")

    safety_limits = LaunchConfiguration("safety_limits")
    safety_pos_margin = LaunchConfiguration("safety_pos_margin")
    safety_k_position = LaunchConfiguration("safety_k_position")

    tf_prefix = LaunchConfiguration("tf_prefix")

    use_fake_hardware = LaunchConfiguration("use_fake_hardware")
    fake_sensor_commands = LaunchConfiguration("fake_sensor_commands")

    headless_mode = LaunchConfiguration("headless_mode")

    use_tool_communication = LaunchConfiguration("use_tool_communication")

    tool_parity = LaunchConfiguration("tool_parity")
    tool_baud_rate = LaunchConfiguration("tool_baud_rate")
    tool_stop_bits = LaunchConfiguration("tool_stop_bits")
    tool_rx_idle_chars = LaunchConfiguration("tool_rx_idle_chars")
    tool_tx_idle_chars = LaunchConfiguration("tool_tx_idle_chars")
    tool_device_name = LaunchConfiguration("tool_device_name")
    tool_tcp_port = LaunchConfiguration("tool_tcp_port")
    tool_voltage = LaunchConfiguration("tool_voltage")

    reverse_ip = LaunchConfiguration("reverse_ip")
    script_command_port = LaunchConfiguration("script_command_port")
    reverse_port = LaunchConfiguration("reverse_port")
    script_sender_port = LaunchConfiguration("script_sender_port")
    trajectory_port = LaunchConfiguration("trajectory_port")

    joint_limit_params = PathJoinSubstitution(
        [
            FindPackageShare(description_package),
            "config",
            ur_type,
            "joint_limits.yaml",
        ]
    )

    physical_params = PathJoinSubstitution(
        [
            FindPackageShare(description_package),
            "config",
            ur_type,
            "physical_parameters.yaml",
        ]
    )

    visual_params = PathJoinSubstitution(
        [
            FindPackageShare(description_package),
            "config",
            ur_type,
            "visual_parameters.yaml",
        ]
    )

    script_filename = PathJoinSubstitution(
        [
            FindPackageShare("ur_client_library"),
            "resources",
            "external_control.urscript",
        ]
    )

    input_recipe_filename = PathJoinSubstitution(
        [
            FindPackageShare("ur_robot_driver"),
            "resources",
            "rtde_input_recipe.txt",
        ]
    )

    output_recipe_filename = PathJoinSubstitution(
        [
            FindPackageShare("ur_robot_driver"),
            "resources",
            "rtde_output_recipe.txt",
        ]
    )

    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [
                    FindPackageShare(description_package),
                    "urdf",
                    description_file,
                ]
            ),
            " ",
            "robot_ip:=", robot_ip,
            " ",
            "joint_limit_params:=", joint_limit_params,
            " ",
            "kinematics_params:=", kinematics_params_file,
            " ",
            "physical_params:=", physical_params,
            " ",
            "visual_params:=", visual_params,
            " ",
            "safety_limits:=", safety_limits,
            " ",
            "safety_pos_margin:=", safety_pos_margin,
            " ",
            "safety_k_position:=", safety_k_position,
            " ",
            "name:=", ur_type,
            " ",
            "script_filename:=", script_filename,
            " ",
            "input_recipe_filename:=", input_recipe_filename,
            " ",
            "output_recipe_filename:=", output_recipe_filename,
            " ",
            "tf_prefix:=", tf_prefix,
            " ",
            "use_fake_hardware:=", use_fake_hardware,
            " ",
            "fake_sensor_commands:=", fake_sensor_commands,
            " ",
            "headless_mode:=", headless_mode,
            " ",
            "use_tool_communication:=", use_tool_communication,
            " ",
            "tool_parity:=", tool_parity,
            " ",
            "tool_baud_rate:=", tool_baud_rate,
            " ",
            "tool_stop_bits:=", tool_stop_bits,
            " ",
            "tool_rx_idle_chars:=", tool_rx_idle_chars,
            " ",
            "tool_tx_idle_chars:=", tool_tx_idle_chars,
            " ",
            "tool_device_name:=", tool_device_name,
            " ",
            "tool_tcp_port:=", tool_tcp_port,
            " ",
            "tool_voltage:=", tool_voltage,
            " ",
            "reverse_ip:=", reverse_ip,
            " ",
            "script_command_port:=", script_command_port,
            " ",
            "reverse_port:=", reverse_port,
            " ",
            "script_sender_port:=", script_sender_port,
            " ",
            "trajectory_port:=", trajectory_port,
        ]
    )

    robot_description = {
        "robot_description": ParameterValue(
            robot_description_content,
            value_type=str,
        )
    }

    robot_description_semantic = {
        "robot_description_semantic": load_file(
            "ros2srrc_ur3_moveit2",
            "config/ur3.srdf",
        )
    }

    kinematics_yaml = load_yaml(
        "ur3_gripper_moveit_config",
        "config/real_robot/kinematics_real.yaml",
    )

    kinematics_yaml = {
        "robot_description_kinematics":
            kinematics_yaml["/**"]["ros__parameters"]
    }

    moveit_controllers = load_yaml(
        "ur3_gripper_moveit_config",
        "config/real_robot/moveit_controllers_real.yaml",
    )

    moveit_controllers = moveit_controllers["/**"]["ros__parameters"]

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
        "capabilities":
            "pilz_industrial_motion_planner/MoveGroupSequenceAction "
            "pilz_industrial_motion_planner/MoveGroupSequenceService"
    }

    ########################################################
    # OMPL
    ########################################################

    ompl_planning = load_yaml(
        "ur3_gripper_moveit_config",
        "config/ompl_planning.yaml",
    )

    ompl_planning = ompl_planning["/**"]["ros__parameters"]

    pilz_cartesian_limits = load_yaml(
        "ros2srrc_robots",
        "ur3/config/pilz_cartesian_limits.yaml",
    )

    joint_limits_yaml = load_yaml(
        "ros2srrc_robots",
        "ur3/config/joint_limits.yaml",
    )

    combined_planning = {
        "robot_description_planning": {
            **joint_limits_yaml,
            **pilz_cartesian_limits,
        }
    }

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
                "use_sim_time": False
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
        ]
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
                "use_sim_time": False
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
        ]
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
                "use_sim_time": False
            },
            {
                "ROB_PARAM": "ur3"
            },
            {
                "ROB_GROUP": "ur3_arm"
            },
        ]
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
            {
                "moveit_controller_manager":
                "moveit_simple_controller_manager/MoveItSimpleControllerManager"
            },
            {
                "publish_robot_description": True,
            },
            {
                "publish_robot_description_semantic": True,
            },
            {
                "use_sim_time": False
            },
        ],
    )

    return [
        move,
        robmove,
        robpose,
        move_group,
    ]


def generate_launch_description():

    declared_arguments = [

        DeclareLaunchArgument(
            "robot_ip",
            default_value="172.22.24.161",
        ),

        DeclareLaunchArgument(
            "reverse_ip",
            default_value="172.22.24.141",
        ),

        DeclareLaunchArgument(
            "ur_type",
            default_value="ur3e",
        ),

        DeclareLaunchArgument(
            "description_package",
            default_value="ur_description",
        ),

        DeclareLaunchArgument(
            "description_file",
            default_value="ur.urdf.xacro",
        ),

        DeclareLaunchArgument(
            "kinematics_params_file",
            default_value=PathJoinSubstitution([
                FindPackageShare("ur3_gripper_moveit_config"),
                "config",
                "real_robot",
                "ur3e_calibration.yaml",
            ]),
        ),

        DeclareLaunchArgument(
            "safety_limits",
            default_value="true",
        ),

        DeclareLaunchArgument(
            "safety_pos_margin",
            default_value="0.15",
        ),

        DeclareLaunchArgument(
            "safety_k_position",
            default_value="20",
        ),

        DeclareLaunchArgument(
            "tf_prefix",
            default_value="",
        ),

        DeclareLaunchArgument(
            "use_fake_hardware",
            default_value="false",
        ),

        DeclareLaunchArgument(
            "fake_sensor_commands",
            default_value="false",
        ),

        DeclareLaunchArgument(
            "headless_mode",
            default_value="false",
        ),

        DeclareLaunchArgument(
            "use_tool_communication",
            default_value="false",
        ),

        DeclareLaunchArgument(
            "tool_parity",
            default_value="0",
        ),

        DeclareLaunchArgument(
            "tool_baud_rate",
            default_value="115200",
        ),

        DeclareLaunchArgument(
            "tool_stop_bits",
            default_value="1",
        ),

        DeclareLaunchArgument(
            "tool_rx_idle_chars",
            default_value="1.5",
        ),

        DeclareLaunchArgument(
            "tool_tx_idle_chars",
            default_value="3.5",
        ),

        DeclareLaunchArgument(
            "tool_device_name",
            default_value="/tmp/ttyUR",
        ),

        DeclareLaunchArgument(
            "tool_tcp_port",
            default_value="54321",
        ),

        DeclareLaunchArgument(
            "tool_voltage",
            default_value="0",
        ),

        DeclareLaunchArgument(
            "script_command_port",
            default_value="50004",
        ),

        DeclareLaunchArgument(
            "reverse_port",
            default_value="50001",
        ),

        DeclareLaunchArgument(
            "script_sender_port",
            default_value="50002",
        ),

        DeclareLaunchArgument(
            "trajectory_port",
            default_value="50003",
        ),

    ]

    return LaunchDescription(
        declared_arguments +
        [OpaqueFunction(function=launch_setup)]
    )