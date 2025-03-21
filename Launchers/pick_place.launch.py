import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.substitutions import FindPackageShare
 
def generate_launch_description():
 
  # Set the path to the Gazebo ROS package
  pkg_gazebo_ros = FindPackageShare(package='gazebo_ros').find('gazebo_ros')
  pkg_ros2srrc = FindPackageShare(package='ros2srrc_launch').find('ros2srrc_launch')
   
  # Set the path to this package.
  pkg_share = FindPackageShare(package='custom_robots').find('custom_robots')

  # Set the path to the world file
  world_file_name = 'warehouse_arm.world'
  worlds_dir = "/opt/jderobot/Worlds"
  world_path = os.path.join(worlds_dir, world_file_name)
   
  # Set the path to the SDF model files.
  gazebo_models_path = os.path.join(pkg_share, 'models')
  os.environ["GAZEBO_MODEL_PATH"] = f"{os.environ.get('GAZEBO_MODEL_PATH', '')}:{':'.join(gazebo_models_path)}"

  ########### YOU DO NOT NEED TO CHANGE ANYTHING BELOW THIS LINE ##############  
  # Launch configuration variables specific to simulation
  headless = LaunchConfiguration('headless')
  use_sim_time = LaunchConfiguration('use_sim_time')
  use_simulator = LaunchConfiguration('use_simulator')
  world = LaunchConfiguration('world')
  package = LaunchConfiguration('package')
  config = LaunchConfiguration('config')
 
  declare_simulator_cmd = DeclareLaunchArgument(
    name='headless',
    default_value='False',
    description='Whether to execute gzclient')
     
  declare_use_sim_time_cmd = DeclareLaunchArgument(
    name='use_sim_time',
    default_value='true',
    description='Use simulation (Gazebo) clock if true')
 
  declare_use_simulator_cmd = DeclareLaunchArgument(
    name='use_simulator',
    default_value='True',
    description='Whether to start the simulator')
 
  declare_world_cmd = DeclareLaunchArgument(
    name='world',
    default_value=world_path,
    description='Full path to the world model file to load')
  
  declare_package_cmd = DeclareLaunchArgument(
    name='package',
    default_value='ros2srrc_ur5',
    description='Full path to the world model file to load')
  
  declare_config_cmd = DeclareLaunchArgument(
    name='config',
    default_value='ur5_2',
    description='Full path to the world model file to load')
    
  # Specify the actions

  # Start Gazebo server
  start_gazebo_server_cmd = IncludeLaunchDescription(
      PythonLaunchDescriptionSource(
          os.path.join(pkg_gazebo_ros, "launch", "gzserver.launch.py")
      ),
      condition=IfCondition(use_simulator),
      launch_arguments={"world": world, "pause": "true"}.items(),
  )

  # Start Gazebo server
  start_ros2srrc_cmd = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(os.path.join(pkg_ros2srrc, 'moveit2', 'moveit2.launch.py')),
    condition=IfCondition(use_simulator),
  )
 
  # Create the launch description and populate
  ld = LaunchDescription()
 
  # Declare the launch options
  ld.add_action(declare_simulator_cmd)
  ld.add_action(declare_use_sim_time_cmd)
  ld.add_action(declare_use_simulator_cmd)
  ld.add_action(declare_world_cmd)
  ld.add_action(declare_package_cmd)
  ld.add_action(declare_config_cmd)
 
  # Add any actions
  ld.add_action(start_gazebo_server_cmd)
  ld.add_action(start_ros2srrc_cmd)
 
  return ld