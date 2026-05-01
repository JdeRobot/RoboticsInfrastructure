import os
import xacro

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_path = get_package_share_directory("ur5_gripper_description")

    xacro_file = os.path.join(
        pkg_path,
        "urdf",
        "ur5_robotiq85_gripper.urdf.xacro"
    )

    controllers_file = os.path.join(
        pkg_path,
        "config",
        "ur5_controllers.yaml"
    )

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
        },
    ).toxml()

    robot_description = {
        "robot_description": robot_description_content
    }

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        parameters=[{"use_sim_time": True}],
        output="screen",
    )

    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name", "ur5",
            "-topic", "robot_description",
            "-x", "0",
            "-y", "0",
            "-z", "0.9",
        ],
        output="screen",
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

    delay_controllers = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_entity,
            on_exit=[joint_state_broadcaster, joint_trajectory_controller],
        )
    )

    static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0", "0", "0.9", "0", "0", "0", "world", "base_link"],
    )

    return LaunchDescription([
        robot_state_publisher,
        clock_bridge,
        static_tf,
        spawn_entity,
        delay_controllers,
    ])