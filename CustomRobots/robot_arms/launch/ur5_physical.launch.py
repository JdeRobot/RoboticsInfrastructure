from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    OpaqueFunction,
)
from launch.substitutions import EnvironmentVariable, LaunchConfiguration
from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterFile

import os
import xacro
import yaml
from ament_index_python.packages import (
    get_package_prefix,
    get_package_share_directory,
)


def load_file(package_name, file_path):
    pkg_path = get_package_share_directory(package_name)
    with open(os.path.join(pkg_path, file_path), "r") as f:
        return f.read()


def load_yaml(package_name, file_path):
    pkg_path = get_package_share_directory(package_name)
    with open(os.path.join(pkg_path, file_path), "r") as f:
        return yaml.safe_load(f)


def launch_setup(context):
    ur_type = LaunchConfiguration("ur_type").perform(context)
    robot_ip = LaunchConfiguration("robot_ip").perform(context)
    reverse_ip = LaunchConfiguration("reverse_ip").perform(context)
    headless_mode = LaunchConfiguration("headless_mode").perform(context)
    kinematics = LaunchConfiguration("kinematics").perform(context)
    gripper = LaunchConfiguration("gripper").perform(context)
    tool_communication = LaunchConfiguration("tool_communication").perform(context)

    if ur_type not in ("ur5", "ur5e"):
        raise RuntimeError(f"UR_TYPE must be ur5 or ur5e, got {ur_type!r}")

    package_dir = get_package_share_directory("custom_robots")
    driver_dir = get_package_share_directory("ur_robot_driver")

    mappings = {
        "name": "ur",
        "ur_type": ur_type,
        "robot_ip": robot_ip,
        "headless_mode": headless_mode,
        "use_tool_communication": tool_communication,
    }
    # Empty values keep the xacro defaults, auto reverse ip and factory kinematics
    if reverse_ip:
        mappings["reverse_ip"] = reverse_ip
    if kinematics:
        mappings["kinematics_params"] = kinematics

    # Same MoveIt stack as the simulated arm with ur_robot_driver in place of Gazebo
    robot_description_content = xacro.process_file(
        os.path.join(package_dir, "models", "ur5", "ur5_physical.urdf.xacro"),
        mappings=mappings,
    ).toxml()
    robot_description = {"robot_description": robot_description_content}

    robot_description_semantic = {
        "robot_description_semantic": load_file(
            "ros2srrc_ur5_moveit2", "config/ur5robotiq_2f85.srdf"
        )
    }

    kinematics_yaml = load_yaml("ur5_gripper_moveit_config", "config/kinematics.yaml")
    kinematics_yaml = {
        "robot_description_kinematics": kinematics_yaml["/**"]["ros__parameters"]
    }

    moveit_controllers = load_yaml(
        "ur5_gripper_moveit_config", "config/moveit_controllers.yaml"
    )["/**"]["ros__parameters"]

    ompl_planning = load_yaml("ur5_gripper_moveit_config", "config/ompl_planning.yaml")[
        "/**"
    ]["ros__parameters"]

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
            **load_yaml("ros2srrc_robots", "ur5/config/joint_limits.yaml"),
            **load_yaml("ros2srrc_robots", "ur5/config/pilz_cartesian_limits.yaml"),
        }
    }

    # The pendant speed slider slows the real arm down so MoveIt must not cancel slow moves
    trajectory_execution = {
        "trajectory_execution.execution_duration_monitoring": False,
    }

    moveit_common = [
        robot_description,
        robot_description_semantic,
        kinematics_yaml,
        ompl_planning,
        {"use_sim_time": False},
        {"ROB_PARAM": "ur5"},
        {"ROB_GROUP": "ur5_manipulator"},
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
        + [moveit_controllers, controller_manager, {"EE_PARAM": "robotiq_2f85"}],
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

    # ur_robot_driver nodes, as in its own ur_control.launch.py
    update_rate_file = os.path.join(driver_dir, "config", f"{ur_type}_update_rate.yaml")
    with open(update_rate_file) as f:
        update_rate = yaml.safe_load(f)["controller_manager"]["ros__parameters"][
            "update_rate"
        ]
    # The controllers file reads it as $(var update_rate)
    context.launch_configurations["update_rate"] = str(update_rate)

    ur_control_node = Node(
        package="ur_robot_driver",
        executable="ur_ros2_control_node",
        parameters=[
            robot_description,
            update_rate_file,
            ParameterFile(
                os.path.join(package_dir, "config", "ur5_physical_controllers.yaml"),
                allow_substs=True,
            ),
        ],
        output="screen",
    )

    dashboard_client = Node(
        package="ur_robot_driver",
        executable="dashboard_client",
        name="dashboard_client",
        output="screen",
        parameters=[{"robot_ip": robot_ip}],
    )

    # Switches the arm controller off while the robot program is not running
    controller_stopper = Node(
        package="ur_robot_driver",
        executable="controller_stopper_node",
        name="controller_stopper",
        output="screen",
        parameters=[
            {"headless_mode": headless_mode == "true"},
            {"joint_controller_active": True},
            {
                "consistent_controllers": [
                    "io_and_status_controller",
                    "force_torque_sensor_broadcaster",
                    "joint_state_broadcaster",
                    "speed_scaling_state_broadcaster",
                ]
            },
        ],
    )

    controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "--controller-manager-timeout",
            "60",
            "joint_state_broadcaster",
            "io_and_status_controller",
            "speed_scaling_state_broadcaster",
            "force_torque_sensor_broadcaster",
            "joint_trajectory_controller",
        ],
    )

    status_node = Node(
        package="ur5_bridge",
        executable="status_node",
        output="screen",
        parameters=[{"headless_mode": headless_mode == "true"}],
    )

    gripper_node = Node(
        package="ur5_bridge",
        executable="gripper_node",
        output="screen",
        parameters=[{"robot_ip": robot_ip, "interface": gripper}],
    )

    nodes = [
        ur_control_node,
        dashboard_client,
        controller_stopper,
        controller_spawner,
        gripper_node,
        status_node,
        robot_state_publisher,
        move_group,
        move,
        robmove,
        robpose,
    ]

    # e-Series tool flange RS485 exposed as /tmp/ttyUR for a gripper without URCap
    if tool_communication == "true":
        nodes.append(
            ExecuteProcess(
                name="ur_tool_comm",
                cmd=[
                    os.path.join(
                        get_package_prefix("ur_client_library"),
                        "lib",
                        "ur_client_library",
                        "tool_communication.py",
                    ),
                    robot_ip,
                    "--tcp-port",
                    "54321",
                    "--device-name",
                    "/tmp/ttyUR",
                ],
                output="screen",
            )
        )

    return nodes


def generate_launch_description():
    declared_arguments = [
        # The real arm sits at the origin of world, the pose is not used
        DeclareLaunchArgument("x", default_value="0"),
        DeclareLaunchArgument("y", default_value="0"),
        DeclareLaunchArgument("z", default_value="0"),
        DeclareLaunchArgument("R", default_value="0"),
        DeclareLaunchArgument("P", default_value="0"),
        DeclareLaunchArgument("Y", default_value="0"),
        DeclareLaunchArgument("entity", default_value="ur5_robotiq"),
        # Each one defaults to an environment variable of the container
        DeclareLaunchArgument(
            "ur_type", default_value=EnvironmentVariable("UR_TYPE", default_value="ur5e")
        ),
        DeclareLaunchArgument(
            "robot_ip",
            default_value=EnvironmentVariable(
                "UR_ROBOT_IP", default_value="192.168.56.101"
            ),
        ),
        # Host address the robot connects back to, empty lets the driver guess it
        DeclareLaunchArgument(
            "reverse_ip",
            default_value=EnvironmentVariable("UR_REVERSE_IP", default_value=""),
        ),
        # true sends the program from here, false needs External Control on the pendant
        DeclareLaunchArgument(
            "headless_mode",
            default_value=EnvironmentVariable("UR_HEADLESS", default_value="true"),
        ),
        # Calibration from ur_calibration, empty uses the factory kinematics
        DeclareLaunchArgument(
            "kinematics",
            default_value=EnvironmentVariable("UR_KINEMATICS", default_value=""),
        ),
        # auto, urcap, rtu or none
        DeclareLaunchArgument(
            "gripper",
            default_value=EnvironmentVariable("UR_GRIPPER", default_value="auto"),
        ),
        DeclareLaunchArgument(
            "tool_communication",
            default_value=EnvironmentVariable(
                "UR_TOOL_COMMUNICATION", default_value="false"
            ),
        ),
    ]

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
