"""
as2_default_ign_gazebo.launch.py
"""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """
    Launch aerostack2 nodes
    """

    # If needed
#    rviz_config = os.path.join(os.getcwd(), 'swarm_config.rviz')
#    print(f'{os.path.isfile(rviz_config)=}')

    sim_config = os.path.join(get_package_share_directory('jderobot_drones'), 'sim_config/ign')

    aerial_platform = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('as2_platform_ign_gazebo'), 'launch'),
            '/ign_gazebo_launch.py']),
        launch_arguments={
            'namespace': LaunchConfiguration('namespace'),
            'use_sim_time': 'true',
            'simulation_config_file': sim_config + '/world.json',
            'platform_config_file': sim_config + '/platform_config_file.yaml'
        }.items(),
    )
    state_estimator = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('as2_state_estimator'), 'launch'),
            '/state_estimator_launch.py']),
        launch_arguments={
            'namespace': LaunchConfiguration('namespace'),
            'use_sim_time': 'true',
            'plugin_name': 'ground_truth',
            'plugin_config_file': sim_config + '/state_estimator_config_file.yaml'
        }.items(),
    )
    motion_controller = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('as2_motion_controller'), 'launch'),
            '/controller_launch.py']),
        launch_arguments={
            'namespace': LaunchConfiguration('namespace'),
            'use_sim_time': 'true',
            'motion_controller_config_file': sim_config + '/motion_controller.yaml',
            'plugin_name': 'pid_speed_controller',
            'plugin_config_file': sim_config + '/motion_controller_plugin.yaml'
        }.items(),
    )
    behaviors = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('as2_behaviors_motion'), 'launch'),
            '/motion_behaviors_launch.py']),
        launch_arguments={
            'namespace': LaunchConfiguration('namespace'),
            'use_sim_time': 'true',
            'takeoff_plugin_name': 'takeoff_plugin_position',
            'go_to_plugin_name': 'go_to_plugin_position',
            'follow_path_plugin_name': 'follow_path_plugin_position',
            'land_plugin_name': 'land_plugin_speed'
        }.items(),
    )
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('as2_ign_gazebo_assets'), 'launch'),
            '/launch_simulation.py']),
        launch_arguments={
            'namespace': LaunchConfiguration('namespace'),
            'use_sim_time': 'true',
            'simulation_config_file': sim_config + '/world.json'
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument('namespace', default_value='drone0',
                              description='Drone namespace.'),
        aerial_platform,
        state_estimator,
        motion_controller,
        behaviors,
#        gazebo
    ])
