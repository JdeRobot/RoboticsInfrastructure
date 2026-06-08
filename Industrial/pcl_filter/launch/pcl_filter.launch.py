from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # Declare launch arguments
    debug_arg = DeclareLaunchArgument(
        'debug',
        default_value='false',
        description='Enable debug mode'
    )
    
    # PCL Filter Server Node
    pcl_filter_node = Node(
        package='pcl_filter',
        executable='pcl_filter_server',
        name='object_detection',
        output='screen',
        parameters=[{
            'debug': LaunchConfiguration('debug')
        }]
    )
    
    return LaunchDescription([
        debug_arg,
        pcl_filter_node
    ])