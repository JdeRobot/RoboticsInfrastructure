import os
import sys

import launch
from launch.conditions import IfCondition
from launch.substitutions import PythonExpression
from ament_index_python.packages import get_package_share_directory
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    # Set the path to the Turtlebot2 ROS package
    pkg_share_dir = FindPackageShare(package='custom_robots').find('custom_robots')

    world_file_name = "hospital.world"
    world = os.path.join(pkg_share_dir, 'worlds', world_file_name)

    gazebo_models_path = os.path.join(pkg_share_dir, 'models')
    gazebo_fuel_models_path = os.path.join(pkg_share_dir, 'fuel_models')
    os.environ["GAZEBO_MODEL_PATH"] = f"{os.environ.get('GAZEBO_MODEL_PATH', '')}:{':'.join(gazebo_models_path)}"
    os.environ["GAZEBO_MODEL_PATH"] = f"{os.environ.get('GAZEBO_MODEL_PATH', '')}:{':'.join(gazebo_fuel_models_path)}"

    gazebo_ros = get_package_share_directory('gazebo_ros')
    gazebo_client = launch.actions.IncludeLaunchDescription(
        launch.launch_description_sources.PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros, 'launch', 'gzclient.launch.py'))
    )
    
    gazebo_server = launch.actions.IncludeLaunchDescription(
        launch.launch_description_sources.PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros, 'launch', 'gzserver.launch.py'))
    )


    ld = launch.LaunchDescription([
        launch.actions.DeclareLaunchArgument(
            'world',
            default_value=[world, ''],
            description='SDF world file'),
        launch.actions.DeclareLaunchArgument(
            name='gui',
            default_value='false'
        ),
        gazebo_server,
        gazebo_client
    ])

    return ld


if __name__ == '__main__':
    generate_launch_description()