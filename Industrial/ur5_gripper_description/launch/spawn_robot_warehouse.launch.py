import os
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    RegisterEventHandler,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import xacro


def generate_launch_description():
    pkg_share_dir = get_package_share_directory("ur5_gripper_description")
    robotiq_pkg_share_dir = get_package_share_directory("robotiq_description")

    # Custom gz_ros2_control for Gazebo Harmonic
    gz_ros2_control_install = "/home/ws/install"
    gz_lib_path = os.path.join(gz_ros2_control_install, "gz_ros2_control", "lib")

    warehouse_models_path = os.path.join(robotiq_pkg_share_dir, "world", "models")
    ur5_share_parent = os.path.dirname(pkg_share_dir)
    robotiq_share_parent = os.path.dirname(robotiq_pkg_share_dir)
    resource_path = (
        ur5_share_parent + ":" + robotiq_share_parent + ":" + warehouse_models_path
    )

    gz_env = {
        "GZ_SIM_RESOURCE_PATH": resource_path,
        "GZ_SIM_SYSTEM_PLUGIN_PATH": gz_lib_path + ":/opt/ros/humble/lib",
        "LD_LIBRARY_PATH": gz_lib_path
        + ":/opt/ros/humble/lib:/usr/lib/x86_64-linux-gnu",
        "DISPLAY": ":2",
    }

    print("DEBUG: GZ_SIM_SYSTEM_PLUGIN_PATH = " + gz_env["GZ_SIM_SYSTEM_PLUGIN_PATH"])

    declared_arguments = [
        DeclareLaunchArgument("ur_type", default_value="ur5"),
        DeclareLaunchArgument("launch_rviz", default_value="true"),
    ]

    xacro_file = os.path.join(pkg_share_dir, "urdf", "ur5_robotiq85_gripper.urdf.xacro")
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
        },
    ).toxml()

    robot_description = {"robot_description": robot_description_content}

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    world_file = os.path.join(
        robotiq_pkg_share_dir, "world", "warehouse_arm_harmonic.world"
    )

    # RAM launches its own GUI client (gz sim -g), so we must NOT launch GUI here
    # This fixes the first-load issue where two GUIs conflict

    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-s", "-r", "-v", "4", world_file],
        output="screen",
        additional_env=gz_env,
        shell=False,
    )

    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic",
            "robot_description",
            "-name",
            "ur5_robotiq",
            "-allow_renaming",
            "true",
            "-x",
            "0.0",
            "-y",
            "0.0",
            "-z",
            "0.9",
            "-R",
            "0.0",
            "-P",
            "0.0",
            "-Y",
            "0.0",
        ],
        output="screen",
    )

    static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0", "0", "0.9", "0", "0", "0", "world", "base_link"],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    gz_ros2_bridge_clock = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    load_joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
        ],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    load_joint_trajectory_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_trajectory_controller", "-c", "/controller_manager"],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    load_gripper_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gripper_controller", "-c", "/controller_manager"],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    moveit_config_package = "ur5_gripper_moveit_config"
    moveit_pkg = get_package_share_directory(moveit_config_package)

    ompl_planning_yaml = os.path.join(moveit_pkg, "config", "ompl_planning.yaml")
    kinematics_yaml = os.path.join(moveit_pkg, "config", "kinematics.yaml")
    srdf_file = os.path.join(moveit_pkg, "srdf", "ur5_robotiq.srdf")
    moveit_controllers = os.path.join(moveit_pkg, "config", "controllers.yaml")

    with open(srdf_file, "r") as f:
        robot_description_semantic = {"robot_description_semantic": f.read()}

    trajectory_execution = {
        "moveit_manage_controllers": True,
        "trajectory_execution.allowed_execution_duration_scaling": 1.2,
        "trajectory_execution.allowed_goal_duration_margin": 0.5,
        "trajectory_execution.allowed_start_tolerance": 0.01,
    }

    planning_scene_monitor_parameters = {
        "publish_planning_scene": True,
        "publish_geometry_updates": True,
        "publish_state_updates": True,
        "publish_transforms_updates": True,
    }

    planning_pipelines_config = {
        "planning_pipelines": ["ompl"],
        "default_planning_pipeline": "ompl",
        "ompl": {
            "planning_plugin": "ompl_interface/OMPLPlanner",
            "request_adapters": "default_planner_request_adapters/AddTimeOptimalParameterization default_planner_request_adapters/ResolveConstraintFrames default_planner_request_adapters/FixWorkspaceBounds default_planner_request_adapters/FixStartStateBounds default_planner_request_adapters/FixStartStateCollision default_planner_request_adapters/FixStartStatePathConstraints",
            "start_state_max_bounds_error": 0.1,
        },
    }

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            ompl_planning_yaml,
            planning_pipelines_config,
            trajectory_execution,
            moveit_controllers,
            planning_scene_monitor_parameters,
            {"use_sim_time": True},
        ],
        condition=IfCondition(LaunchConfiguration("launch_rviz")),
    )

    rviz_config_file = os.path.join(moveit_pkg, "rviz", "moveit.rviz")
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        parameters=[
            robot_description,
            robot_description_semantic,
            ompl_planning_yaml,
            kinematics_yaml,
            {"use_sim_time": True},
        ],
        condition=IfCondition(LaunchConfiguration("launch_rviz")),
    )

    delay_spawn = TimerAction(period=5.0, actions=[spawn_entity])

    delay_jsb = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_entity, on_exit=[load_joint_state_broadcaster]
        )
    )
    delay_jtc = RegisterEventHandler(
        OnProcessExit(
            target_action=load_joint_state_broadcaster,
            on_exit=[load_joint_trajectory_controller],
        )
    )
    delay_gc = RegisterEventHandler(
        OnProcessExit(
            target_action=load_joint_trajectory_controller,
            on_exit=[load_gripper_controller],
        )
    )
    delay_mg = TimerAction(period=10.0, actions=[move_group_node])
    delay_rviz = TimerAction(period=12.0, actions=[rviz_node])

    return LaunchDescription(
        declared_arguments
        + [
            gazebo,
            robot_state_publisher,
            static_tf,
            gz_ros2_bridge_clock,
            delay_spawn,
            delay_jsb,
            delay_jtc,
            delay_gc,
            delay_mg,
            delay_rviz,
        ]
    )