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
import tempfile
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
        "ur3",
        "ur3_servo.urdf.xacro",
    )

    controllers_file = os.path.join(package_dir, "config", "ur3_controllers.yaml")

    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "ur_type": "ur3",
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
            "ros2srrc_ur3_moveit2", "config/ur3robotiq_2f85.srdf"
        )
    }

    # =========================
    # KINEMATICS
    # =========================
    kinematics_yaml = load_yaml("ur3_gripper_moveit_config", "config/kinematics.yaml")

    kinematics_yaml = {
        "robot_description_kinematics": kinematics_yaml["/**"]["ros__parameters"]
    }

    # =========================
    # CONTROLLERS (MoveIt)
    # =========================
    moveit_controllers = load_yaml(
        "ur3_gripper_moveit_config", "config/moveit_controllers.yaml"
    )

    ompl_planning = load_yaml("ur3_gripper_moveit_config", "config/ompl_planning.yaml")

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
        "ros2srrc_robots", "ur3/config/pilz_cartesian_limits.yaml"
    )

    joint_limits_yaml = load_yaml("ros2srrc_robots", "ur3/config/joint_limits.yaml")

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
            {"ROB_PARAM": "ur3"},
            {"EE_PARAM": "robotiq_2f85"},
            {"ROB_GROUP": "ur3_arm"},
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
            {"ROB_PARAM": "ur3"},
            {"ROB_GROUP": "ur3_arm"},
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
            {"ROB_PARAM": "ur3"},
            {"ROB_GROUP": "ur3_arm"},
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
            "ur3_robotiq",
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

    nodes.append(robot_state_publisher)
    nodes.append(static_tf)
    nodes.append(spawn_robot)

    if sensor == "camera":
        # Lazy bridge so gz only renders a camera while someone subscribes to it
        camera_topics = [
            (f"/{camera}/{topic}", ros_type, gz_type)
            for camera in ("hand_camera", "base_camera")
            for topic, ros_type, gz_type in (
                ("image", "sensor_msgs/msg/Image", "gz.msgs.Image"),
                ("camera_info", "sensor_msgs/msg/CameraInfo", "gz.msgs.CameraInfo"),
            )
        ]
        camera_config = os.path.join(
            tempfile.mkdtemp(prefix="ur3_"), "camera_bridge.yaml"
        )
        with open(camera_config, "w") as fh:
            yaml.safe_dump(
                [
                    {
                        "ros_topic_name": topic,
                        "gz_topic_name": topic,
                        "ros_type_name": ros_type,
                        "gz_type_name": gz_type,
                        "direction": "GZ_TO_ROS",
                        "lazy": True,
                    }
                    for topic, ros_type, gz_type in camera_topics
                ],
                fh,
            )

        camera_bridge = Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            name="camera_bridge",
            parameters=[{"config_file": camera_config}],
            output="screen",
        )

        nodes.append(camera_bridge)

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

    # MoveIt Servo stays loaded and the HAL starts or stops it through its services
    servo_yaml = load_yaml("ur3_gripper_moveit_config", "config/ur_servo.yaml")

    servo_node = Node(
        package="moveit_servo",
        executable="servo_node_main",
        parameters=[
            {"moveit_servo": servo_yaml},
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            combined_planning,
            {"use_sim_time": True},
        ],
        output="screen",
    )

    nodes.append(servo_node)

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
