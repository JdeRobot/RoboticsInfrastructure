#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import TimerAction
from launch_ros.actions import Node


def generate_launch_description():

    rviz_config = (
        "/home/ws/src/Industrial/"
        "ros2_SimRealRobotControl_gz/"
        "packages/ur3/"
        "ros2srrc_ur3_moveit2/"
        "rviz/moveit.rviz"
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=[
            "-d",
            rviz_config,
        ],
        parameters=[
            {
                "use_sim_time": False,
            }
        ],
    )

    return LaunchDescription(
        [
            TimerAction(
                period=2.0,
                actions=[rviz],
            )
        ]
    )