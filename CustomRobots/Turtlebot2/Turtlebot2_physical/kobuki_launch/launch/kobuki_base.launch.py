import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
import yaml

def generate_launch_description():
    shared_dir = get_package_share_directory('kobuki_launch')

    params_file = os.path.join(shared_dir, 'config', 'kobuki_node_params.yaml')
    with open(params_file, 'r') as f:
        kobuki_params = yaml.safe_load(f)['kobuki_ros_node']['ros__parameters']

    kobuki_cmd = Node(package='kobuki_node',
        executable='kobuki_ros_node',
        output='screen',
        parameters=[kobuki_params],
        )

    ld = LaunchDescription()

    ld.add_action(kobuki_cmd)
  
    return ld
