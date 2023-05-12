import os
import launch, launch_ros
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
  
  # Set (x, y, z) default position of turtlebot2
  x_pos = LaunchConfiguration('-x', default='0')
  y_pos = LaunchConfiguration('-y', default='0')
  z_pos = LaunchConfiguration('-z', default='0')
  
  # Find Turtlebot2 package
  pkg_share = launch_ros.substitutions.FindPackageShare(package='custom_robots').find('custom_robots')

  # Find Urdf File
  urdf_file = os.path.join(pkg_share, 'urdf/amazon_robot.urdf')
  
  # Open Urdf file
  with open(urdf_file, 'r') as info:
    robot_desc = info.read()
  
  # Robot description Turtlebot2
  turtlebot2_model = Node(
    package='robot_state_publisher',
    executable='robot_state_publisher',
    parameters=[{'robot_description': robot_desc}],
    arguments=[urdf_file]
  )

  # TF Tree
  joint_state_publisher_node = Node(
    package='joint_state_publisher',
    executable='joint_state_publisher',
    name='joint_state_publisher'
  )

  # Spawn Turtlebot2
  spawn_entity_node = Node(
    package='gazebo_ros',
    executable='spawn_entity.py',
    name='entity_spawner',
    output='screen',
    arguments=["-topic", "/robot_description", "-entity", "amazon_robot", "-x", x_pos, "-y", y_pos, "-z", z_pos]
  )

  ld = LaunchDescription()
  ld.add_action(turtlebot2_model)
  ld.add_action(joint_state_publisher_node)
  ld.add_action(spawn_entity_node)

  return ld