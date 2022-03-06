import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import ExecuteProcess, DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node


def generate_launch_description():

  ld = LaunchDescription()

  use_sim_time = LaunchConfiguration('use_sim_time', default='True')
  
  pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

  gazebo_server = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(os.path.join(pkg_gazebo_ros, 'launch', 'gzserver.launch.py'))
  )

  gazebo_client = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(os.path.join(pkg_gazebo_ros, 'launch', 'gzclient.launch.py'))
  )

  execute_process = ExecuteProcess(
    cmd=['ros2', 'param', 'set', '/gazebo', 'use_sim_time', use_sim_time], output='screen')
  
  ld.add_action(gazebo_server)
  ld.add_action(gazebo_client)
  ld.add_action(execute_process)

  return ld
