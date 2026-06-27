from launch.actions import DeclareLaunchArgument, OpaqueFunction
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

    package_dir = get_package_share_directory("custom_robots")

    nodes = []

    # =========================
    # ROBOT DESCRIPTION (URDF)
    # =========================
    xacro_file = os.path.join(
        package_dir,
        "models",
        "ur10",
        "ur10_suction.urdf.xacro",
    )

    controllers_file = os.path.join(package_dir, "config", "ur10_suction_controllers.yaml")

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

    # =========================
    # SRDF (SEMANTIC)
    # =========================
    robot_description_semantic = {
        "robot_description_semantic": load_file(
            "custom_robots", "config/ur10_suction.srdf"
        )
    }

    # =========================
    # KINEMATICS
    # =========================
    kinematics_yaml = load_yaml(
        "custom_robots", "config/ur10_suction_kinematics.yaml"
    )

    kinematics_yaml = {
        "robot_description_kinematics": kinematics_yaml["/**"]["ros__parameters"]
    }

    # =========================
    # CONTROLLERS (MoveIt)
    # =========================
    moveit_controllers = load_yaml(
        "custom_robots", "config/ur10_suction_moveit_controllers.yaml"
    )

    ompl_planning = load_yaml(
        "custom_robots", "config/ur10_suction_ompl_planning.yaml"
    )

    ompl_planning = ompl_planning["/**"]["ros__parameters"]

    moveit_controllers = moveit_controllers["/**"]["ros__parameters"]

    planning_pipelines_config = {
        "planning_pipelines": ["ompl", "pilz_industrial_motion_planner"],
        "default_planning_pipeline": "pilz_industrial_motion_planner",
        "ompl": {
            "planning_plugin": "ompl_interface/OMPLPlanner",
            # AddTimeOptimalParameterization assigns timestamps to the planned
            # waypoints. Without it, OMPL plans have all-zero times and the
            # joint_trajectory_controller rejects them ("Time between points ...
            # is not strictly increasing").
            "request_adapters": "default_planner_request_adapters/AddTimeOptimalParameterization "
            "default_planner_request_adapters/ResolveConstraintFrames "
            "default_planner_request_adapters/FixWorkspaceBounds "
            "default_planner_request_adapters/FixStartStateBounds "
            "default_planner_request_adapters/FixStartStateCollision "
            "default_planner_request_adapters/FixStartStatePathConstraints",
            "start_state_max_bounds_error": 0.1,
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

    pilz_cartesian_limits = load_yaml(
        "ros2srrc_robots", "ur10/config/pilz_cartesian_limits.yaml"
    )

    joint_limits_yaml = load_yaml("ros2srrc_robots", "ur10/config/joint_limits.yaml")

    combined_planning = {
        "robot_description_planning": {**joint_limits_yaml, **pilz_cartesian_limits}
    }

    # =========================
    # NODES
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
            {"ROB_PARAM": "ur10"},
            # Suction has no actuated end-effector joint, so there is no
            # ros2srrc_endeffectors/ls_vgr/config/joint_specifications.yaml to load.
            # "none" makes the move server skip the EE block (it otherwise crashes
            # with YAML::BadFile). Gripping is handled by gz_link_attacher, not MoveG.
            {"EE_PARAM": "none"},
            {"MOVE_GROUP": "ur10_arm"},
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
            {"ROB_PARAM": "ur10"},
            {"MOVE_GROUP": "ur10_arm"},
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
            {"ROB_PARAM": "ur10"},
            {"MOVE_GROUP": "ur10_arm"},
        ],
    )

    nodes.append(move)
    nodes.append(robmove)
    nodes.append(robpose)

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
        arguments=[x, y, z, R, P, Y, "world", "base_link"],
    )

    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic",
            "robot_description",
            "-name",
            "ur10_suction",
            "-x",
            x,
            "-y",
            y,
            "-z",
            z,
            "-R",
            R,
            "-P",
            P,
            "-Y",
            Y,
        ],
        output="screen",
    )

    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock@gz.msgs.Clock"],
        parameters=[{"use_sim_time": True}],
    )

    nodes.append(robot_state_publisher)
    nodes.append(static_tf)
    nodes.append(spawn_robot)
    nodes.append(clock_bridge)

    # =========================
    # CONTROLLERS (arm only — no gripper)
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

    nodes.append(joint_state_broadcaster)
    nodes.append(joint_trajectory_controller)

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
            move_group_capabilities,
            moveit_controllers,
            combined_planning,
            {"use_sim_time": True},
        ],
    )

    nodes.append(move_group)

    # =========================
    # RVIZ
    # =========================
    rviz_config_file = os.path.join(package_dir, "config", "ur10_moveit.rviz")
    
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        parameters=[
            robot_description,
            robot_description_semantic,
            ompl_planning,
            kinematics_yaml,
            {"use_sim_time": True},
        ],
    )
    
    nodes.append(rviz_node)

    return nodes


def generate_launch_description():
    declared_arguments = [
        DeclareLaunchArgument("x", default_value="0"),
        DeclareLaunchArgument("y", default_value="0"),
        DeclareLaunchArgument("z", default_value="0.9"),
        DeclareLaunchArgument("R", default_value="0"),
        DeclareLaunchArgument("P", default_value="0"),
        DeclareLaunchArgument("Y", default_value="0"),
    ]

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
