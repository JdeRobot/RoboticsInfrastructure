import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    AppendEnvironmentVariable
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    
    package_dir = get_package_share_directory('custom_robots')
    gz_model_path = os.path.join(package_dir,
        'models'
    )

    sdf_file = os.path.join(package_dir, 'models', 'roombaROS_harmonic', 'model.sdf')
    with open(sdf_file, 'r') as infp:
        robot_desc = infp.read()

    robot_launch_dir = "/opt/jderobot/Launchers/vacuum_cleaner_harmonic"
    ros_gz_sim = get_package_share_directory('ros_gz_sim')
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    x_pose = LaunchConfiguration('x_pose', default='-1')
    y_pose = LaunchConfiguration('y_pose', default='1.5')
    z_pose = LaunchConfiguration('z_pose', default='0.0')

    world_file_name = "roomba_1_house_harmonic.world"
    worlds_dir = "/opt/jderobot/Worlds"
    world_path = os.path.join(worlds_dir, world_file_name)

    gazebo_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, 'launch', 'gz_sim.launch.py')),
        launch_arguments={
            'gz_args': ['-r -s -v4 ', world_path],
            'on_exit_shutdown': 'true'
        }.items()
    )

    robot_state_publisher_cmd = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'robot_description': robot_desc},
        ]
    )

    spawn_robot_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(robot_launch_dir, 'spawn_robot.launch.py')
        ),
        launch_arguments={
            'x_pose': x_pose,
            'y_pose': y_pose,
            'z_pose': z_pose
        }.items()
    )

    world_entity_cmd = Node(package='ros_gz_sim', executable='create',
                            arguments=['-name',
                                       'world',
                                       '-file',
                                       world_path
                                       ],
                            output='screen')

    ld = LaunchDescription()

    ld.add_action(SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', gz_model_path))
    set_env_vars_resources = AppendEnvironmentVariable('GZ_SIM_RESOURCE_PATH', os.path.join(package_dir,'models'))
    ld.add_action(set_env_vars_resources)
    ld.add_action(gazebo_server)
    ld.add_action(robot_state_publisher_cmd)
    ld.add_action(world_entity_cmd)
    ld.add_action(spawn_robot_cmd)

    return ld
