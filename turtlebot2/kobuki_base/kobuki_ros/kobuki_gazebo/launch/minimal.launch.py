import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import ExecuteProcess, DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node


def generate_launch_description():

  kobuki_gazebo_pkg = get_package_share_directory('kobuki_gazebo')

  empty_world_launch = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(os.path.join(kobuki_gazebo_pkg, 'launch', 'empty_world.launch.py'))
  )

  spawn_model_launch = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(os.path.join(kobuki_gazebo_pkg, 'launch', 'spawn_model.launch.py'))
  )

  ld = LaunchDescription()

  ld.add_action(empty_world_launch)
  ld.add_action(spawn_model_launch)

  return ld