from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import TimerAction


def generate_launch_description():

    driver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            "/opt/ros/humble/share/ur_robot_driver/launch/ur_control.launch.py"
        ),
        launch_arguments={
            "ur_type": "ur3e",
            "robot_ip": "172.22.24.161",
            "reverse_ip": "172.22.24.141",
            "launch_rviz": "false",
        }.items(),
    )

    moveit = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            "/home/ws/src/CustomRobots/robot_arms/launch/ur3e_real.launch.py"
        )
    )

    return LaunchDescription([
        driver,
        TimerAction(
            period=5.0,
            actions=[moveit],
        ),
    ])