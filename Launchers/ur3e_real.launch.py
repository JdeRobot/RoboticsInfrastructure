from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():

    moveit = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            "/home/ws/src/CustomRobots/robot_arms/launch/ur3e_real.launch.py"
        )
    )

    return LaunchDescription([
        moveit,
    ])