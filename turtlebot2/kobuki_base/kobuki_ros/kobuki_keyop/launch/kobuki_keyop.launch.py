import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import ExecuteProcess, DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node


def generate_launch_description():

  kobuki_node_pkg = get_package_share_directory('kobuki_node')

  kobuki_node_launch = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(os.path.join(kobuki_node_pkg, 'launch', 'kobuki_node-launch.py'))
  )

  kobuki_keyop_node = Node(
    package='kobuki_keyop',
    executable='kobuki_keyop_node',
    name='kobuki_keyop',
    prefix='xterm -e',
    output='screen'
  )

  ld = LaunchDescription()

  ld.add_action(kobuki_node_launch)
  ld.add_action(kobuki_keyop_node)

  return ld