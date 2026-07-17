from launch.actions import (
    IncludeLaunchDescription,
    DeclareLaunchArgument,
    SetEnvironmentVariable,
)
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch import LaunchDescription
from launch_ros.actions import Node

import os
import xacro
import yaml
from ament_index_python.packages import get_package_share_directory
from launch.actions import DeclareLaunchArgument, OpaqueFunction


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
    gz_sensor = LaunchConfiguration("sensor")

    package_dir = get_package_share_directory("custom_robots")

    sensor = gz_sensor.perform(context)

    nodes = []

    # =========================
    # ROBOT DESCRIPTION (URDF)
    # =========================
    xacro_file = os.path.join(
        package_dir,
        "models",
        "ur5",
        "ur5.urdf.xacro",
    )

    controllers_file = os.path.join(package_dir, "config", "ur5_controllers.yaml")

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
            "camera": "true" if sensor == "camera" else "false",
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

    pilz_cartesian_limits = load_yaml(
        "ros2srrc_robots", "ur5/config/pilz_cartesian_limits.yaml"
    )

    joint_limits_yaml = load_yaml("ros2srrc_robots", "ur5/config/joint_limits.yaml")

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
            {"ROB_PARAM": "ur5"},
            {"EE_PARAM": "robotiq_2f85"},
            {"ROB_GROUP": "ur5_manipulator"},
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
            {"ROB_GROUP": "ur5_manipulator"},
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
            {"ROB_GROUP": "ur5_manipulator"},
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
            "ur5_robotiq",
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
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock]"],
        parameters=[{"use_sim_time": True}],
    )

    nodes.append(robot_state_publisher)
    nodes.append(static_tf)
    nodes.append(spawn_robot)
    nodes.append(clock_bridge)

    if sensor == "camera":
        camera_bridge = Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            arguments=[
                "/hand_camera/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo",
                "/base_camera/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo",
            ],
            output="screen",
        )

        gz_ros2_image_bridge = Node(
            package="ros_gz_image",
            executable="image_bridge",
            arguments=["/hand_camera/image"],
            output="screen",
        )

        gz_ros2_base_image_bridge = Node(
            package="ros_gz_image",
            executable="image_bridge",
            arguments=["/base_camera/image"],
            output="screen",
        )

        nodes.append(camera_bridge)
        nodes.append(gz_ros2_image_bridge)
        nodes.append(gz_ros2_base_image_bridge)

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

    nodes.append(joint_state_broadcaster)
    nodes.append(joint_trajectory_controller)
    nodes.append(gripper_controller)

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
    # LAUNCH
    # =========================

    return nodes


def generate_launch_description():
    declared_arguments = [
        DeclareLaunchArgument("x", default_value="0"),
        DeclareLaunchArgument("y", default_value="0"),
        DeclareLaunchArgument("z", default_value="0.9"),
        DeclareLaunchArgument("R", default_value="0"),
        DeclareLaunchArgument("P", default_value="0"),
        DeclareLaunchArgument("Y", default_value="0"),
        DeclareLaunchArgument("sensor", default_value="none"),
    ]

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
