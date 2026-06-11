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

    sensor = gz_sensor.perform(context)

    nodes = []

    # =========================
    # ROBOT DESCRIPTION (URDF)
    # =========================
    xacro_file = os.path.join(
        get_package_share_directory("ros2srrc_ur3_gazebo"),
        "urdf",
        "ur3_robotiq_2f85.urdf.xacro",
    )

    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "bringup": "false",
            "hmi": "false",
            "robot_ip": "0.0.0.0",
            "EE": "true",
            "EE_name": "robotiq_2f85",
            "camera": "true" if sensor == "camera" else "false",
            "script_filename": "none",
            "input_recipe_filename": "none",
            "output_recipe_filename": "none",
        },
    ).toxml()

    robot_description = {"robot_description": robot_description_content}

    # =========================
    # ENVIROMENT
    # =========================

    gz_ros2_control_path = "/home/ws/install/gz_ros2_control/lib"
    gz_link_attacher_path = "/home/ws/install/gz_link_attacher/lib"

    gz_plugin_path = (
        gz_link_attacher_path + ":" + gz_ros2_control_path + ":" + "/opt/ros/humble/lib"
    )

    resource_path = (
        os.path.dirname(get_package_share_directory("ros2srrc_ur3_gazebo"))
        + ":"
        + os.path.dirname(get_package_share_directory("ros2srrc_robots"))
        + ":"
        + os.path.dirname(get_package_share_directory("ros2srrc_endeffectors"))
        + ":"
        + os.path.dirname(get_package_share_directory("robotiq_description"))
        + ":"
        + os.path.join(
            get_package_share_directory("robotiq_description"),
            "world",
            "models",
        )
    )

    set_resource_path = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH", value=resource_path
    )

    set_gz_plugin_path = SetEnvironmentVariable(
        name="GZ_SIM_SYSTEM_PLUGIN_PATH", value=gz_plugin_path
    )

    existing_ld = os.environ.get("LD_LIBRARY_PATH", "")

    set_ld_library_path = SetEnvironmentVariable(
        name="LD_LIBRARY_PATH",
        value=gz_plugin_path + ":/usr/lib/x86_64-linux-gnu:" + existing_ld,
    )

    nodes.append(set_resource_path)
    nodes.append(set_gz_plugin_path)
    nodes.append(set_ld_library_path)

    # =========================
    # SRDF (SEMANTIC)
    # =========================
    robot_description_semantic = {
        "robot_description_semantic": load_file(
            "ros2srrc_ur3_moveit2",
            "config/ur3robotiq_2f85.srdf"
        )
    }

    # =========================
    # KINEMATICS
    # =========================
    kinematics_yaml = {
        "robot_description_kinematics": load_yaml(
            "ros2srrc_robots",
            "ur3/config/kinematics.yaml"
        )
    }


    # =========================
    # Moveit controller
    # =========================
    moveit_controllers = load_yaml(
        "ros2srrc_robots",
        "ur3/config/moveit_controllers.yaml"
    )

    moveit_controllers = moveit_controllers["/**"]["ros__parameters"]

    ompl_planning = load_yaml(
        "ros2srrc_robots",
        "ur3/config/ompl_planning.yaml"
    )

    ompl_planning = ompl_planning["/**"]["ros__parameters"]
            
    joint_limits_yaml = load_yaml(
        "ros2srrc_robots",
        "ur3/config/joint_limits.yaml"
    )

    pilz_cartesian_limits = load_yaml(
        "ros2srrc_robots",
        "ur3/config/pilz_cartesian_limits.yaml"
    )

    combined_planning = {
        "robot_description_planning":
            {**joint_limits_yaml, **pilz_cartesian_limits}
    }

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
                "moveit_controller_manager":
                "moveit_simple_controller_manager/MoveItSimpleControllerManager"
            },
            combined_planning,
            {"use_sim_time": True},
            {"ROB_PARAM": "ur3"},
            {"EE_PARAM": "robotiq_2f85"},
            {"MOVE_GROUP": "ur3_arm"},
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
                "moveit_controller_manager":
                "moveit_simple_controller_manager/MoveItSimpleControllerManager"
            },
            {"use_sim_time": True},
            {"ROB_PARAM": "ur3"},
            {"MOVE_GROUP": "ur3_arm"},
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
            {"MOVE_GROUP": "ur3_arm"},
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
            "ur3",
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

    sausage_spawner = Node(
        package="custom_robots",
        executable="spawn_sausage.py",
        name="box_spawner",
        output="screen",
    )

    nodes.append(robot_state_publisher)
    nodes.append(static_tf)
    nodes.append(spawn_robot)
    nodes.append(clock_bridge)
    #nodes.append(sausage_spawner)

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
