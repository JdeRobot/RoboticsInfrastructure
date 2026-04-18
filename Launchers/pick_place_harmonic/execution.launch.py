from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    move = Node(
        package="ros2srrc_execution",
        executable="move",
        name="move_action_server",
        output="screen"
    )

    robmove = Node(
        package="ros2srrc_execution",
        executable="robmove",
        name="Robmove",
        output="screen"
    )

    robpose = Node(
        package="ros2srrc_execution",
        executable="robpose",
        name="robpose",
        output="screen"
    )

    return LaunchDescription([
        move,
        robmove,
        robpose
    ])