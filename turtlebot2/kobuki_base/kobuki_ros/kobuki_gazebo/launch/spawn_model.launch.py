import os
import launch, launch_ros
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
  
  use_sim_time = LaunchConfiguration('use_sim_time', default='True')
  
  pkg_share = launch_ros.substitutions.FindPackageShare(package='kobuki_description').find('kobuki_description')
  urdf_file = os.path.join(pkg_share, 'urdf/kobuki.urdf')
  
  with open(urdf_file, 'r') as infp:
    robot_desc = infp.read()

  kobuki_model = Node(
    package='robot_state_publisher',
    executable='robot_state_publisher',
    parameters=[{'robot_description': robot_desc}],
    arguments=[urdf_file]
  )

  joint_state_publisher_node = Node(
    package='joint_state_publisher',
    executable='joint_state_publisher',
    name='joint_state_publisher'
  )

  spawn_entity = ExecuteProcess(
    cmd=['ros2', 'run', 'gazebo_ros', 'spawn_entity.py', '-topic', '/robot_description', '-entity', 'kobuki'], output='screen')

  ld = LaunchDescription()
  ld.add_action(kobuki_model)
  ld.add_action(joint_state_publisher_node)
  ld.add_action(spawn_entity)

  return ld
