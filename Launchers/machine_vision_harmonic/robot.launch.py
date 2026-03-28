import os
import xacro

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import RegisterEventHandler, TimerAction
from launch.event_handlers import OnProcessExit
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_path = get_package_share_directory("ur5_gripper_description")

    xacro_file = os.path.join(
        pkg_path,
        "urdf",
        "ur5_machine_vision.urdf.xacro"
    )

    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "sim_gz": "true"
        }
    ).toxml()

    robot_description = {"robot_description": robot_description_content}

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic", "robot_description",
            "-name", "ur5",
            "-x", "0",
            "-y", "0",
            "-z", "0.9",
        ],
        output="screen",
    )

    static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0", "0", "0.9", "0", "0", "0", "world", "base_link"],
    )

    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        parameters=[{"use_sim_time": True}],
    )

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

    delay_spawn = TimerAction(period=3.0, actions=[spawn_entity])

    delay_js = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_entity,
            on_exit=[joint_state_broadcaster],
        )
    )

    delay_traj = RegisterEventHandler(
        OnProcessExit(
            target_action=joint_state_broadcaster,
            on_exit=[joint_trajectory_controller],
        )
    )

    return LaunchDescription([
        robot_state_publisher,
        static_tf,
        clock_bridge,
        delay_spawn,
        delay_js,
        delay_traj,
    ])