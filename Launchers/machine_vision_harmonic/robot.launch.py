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

    gz_ros2_control_install = "/home/ws/install"
    gz_lib_path = os.path.join(gz_ros2_control_install, "gz_ros2_control", "lib")

    machine_vision_models_path = "/opt/jderobot/Worlds/models"

    resource_path = machine_vision_models_path

    gz_env = {
        "GZ_SIM_RESOURCE_PATH": resource_path,
        "GZ_SIM_SYSTEM_PLUGIN_PATH": (
            "/home/ws/install/gz_link_attacher/lib:"
            + gz_lib_path
            + ":/opt/ros/humble/lib"
        ),
        "LD_LIBRARY_PATH": "/home/ws/install/gz_link_attacher/lib:"
        + gz_lib_path
        + ":/opt/ros/humble/lib:/usr/lib/x86_64-linux-gnu:"
        + os.environ.get("LD_LIBRARY_PATH", ""),
    }

    declared_arguments = [
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
            "sim_gz": "true",
            "simulation_controllers": controllers_file,
        },
    ).toxml()

    robot_description = {"robot_description": robot_description_content}

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[robot_description, {"use_sim_time": True}],
        output="screen",
    )

    world_file = "/opt/jderobot/Worlds/machine_vision_harmonic.world"

    env = os.environ.copy()
    env.update(gz_env)

    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-r", "-v", "4", world_file],
        output="screen",
        additional_env=env,
    )

    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic", "robot_description",
            "-name", "ur5",
            "-x", "0.0",
            "-y", "0.0",
            "-z", "0.75",
        ],
        output="screen",
    )

    static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0", "0", "0", "0", "0", "0", "world", "base_link"],
    )

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
    )

    jsb = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
    )

    jtc = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_trajectory_controller"],
    )

    gripper = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gripper_controller"],
    )

    moveit_pkg = get_package_share_directory("ur5_gripper_moveit_config")

    move_group = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        parameters=[robot_description, {"use_sim_time": True}],
        condition=IfCondition(LaunchConfiguration("launch_rviz")),
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", os.path.join(moveit_pkg, "rviz", "moveit.rviz")],
        condition=IfCondition(LaunchConfiguration("launch_rviz")),
    )

    delay_spawn = TimerAction(period=5.0, actions=[spawn_entity])

    delay_jsb = RegisterEventHandler(
        OnProcessExit(target_action=spawn_entity, on_exit=[jsb])
    )

    delay_jtc = RegisterEventHandler(
        OnProcessExit(target_action=jsb, on_exit=[jtc])
    )

    delay_gripper = RegisterEventHandler(
        OnProcessExit(target_action=jtc, on_exit=[gripper])
    )

    return LaunchDescription(
        declared_arguments + [
            gazebo,
            robot_state_publisher,
            static_tf,
            bridge,
            delay_spawn,
            delay_jsb,
            delay_jtc,
            delay_gripper,
            move_group,
            rviz,
        ]
    )