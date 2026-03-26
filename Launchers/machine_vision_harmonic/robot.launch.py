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
        "ur5_robotiq_2f85_with_cams.urdf.xacro"
    )

    doc = xacro.parse(open(xacro_file))
    xacro.process_doc(doc, mappings={
        "hmi": "true"
    })

    robot_description = {
        "robot_description": doc.toxml()
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
            "-z", "0.01",
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

    return LaunchDescription([
        robot_state_publisher,
        clock_bridge,
        spawn_entity,
        delay_controllers,
    ])