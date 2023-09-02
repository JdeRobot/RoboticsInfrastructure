"""
as2_default_classic_gazebo.launch.py
"""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """
    Launch micro_xrce and aerostack2 nodes
    """

    # If needed
#    rviz_config = os.path.join(os.getcwd(), 'swarm_config.rviz')
#    print(f'{os.path.isfile(rviz_config)=}')
    micro_xrce_cmd = ['MicroXRCEAgent', 'udp4', '-p', '8888']

    micro_xrce = ExecuteProcess(
    cmd = micro_xrce_cmd,
    output = 'screen'
    )

    sim_config = os.path.join(get_package_share_directory('jderobot_drones'), 'sim_config/px4_classic')

    aerial_platform = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('as2_platform_pixhawk'), 'launch'),
            '/pixhawk_launch.py']),
        launch_arguments={
            'namespace': LaunchConfiguration('namespace'),
            'use_sim_time': 'false',
            'simulation_config_file': LaunchConfiguration('world_file'),
            'platform_config_file': sim_config + '/platform_config.yaml'
        }.items(),
    )
    state_estimator = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('as2_state_estimator'), 'launch'),
            '/state_estimator_launch.py']),
        launch_arguments={
            'namespace': LaunchConfiguration('namespace'),
            'use_sim_time': 'false',
            'plugin_name': 'raw_odometry',
            'plugin_config_file': sim_config + '/state_estimator_odom.yaml'
        }.items(),
    )
    motion_controller = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('as2_motion_controller'), 'launch'),
            '/controller_launch.py']),
        launch_arguments={
            'namespace': LaunchConfiguration('namespace'),
            'use_sim_time': 'false',
            'motion_controller_config_file': sim_config + '/motion_controller.yaml',
            'plugin_name': 'pid_speed_controller',
            'plugin_config_file': sim_config + '/pid_speed_controller.yaml'
        }.items(),
    )
    behaviors = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('as2_behaviors_motion'), 'launch'),
            '/motion_behaviors_launch.py']),
        launch_arguments={
            'namespace': LaunchConfiguration('namespace'),
            'use_sim_time': 'false',
            'takeoff_plugin_name': 'takeoff_plugin_position',
            'go_to_plugin_name': 'go_to_plugin_position',
            'follow_path_plugin_name': 'follow_path_plugin_position',
            'land_plugin_name': 'land_plugin_speed'
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument('namespace', default_value='drone0',
                              description='Drone namespace.'),
        DeclareLaunchArgument('world_file', default_value=sim_config + '/world.json',
                              description='json world file'),
        micro_xrce,
        aerial_platform,
        state_estimator,
        motion_controller
        # behaviors
    ])
