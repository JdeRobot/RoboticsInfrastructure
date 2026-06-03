"""
Launch file for the drone cat-mouse chase exercise.
maintainer: Anish Kumar (anishkumar59085@gmail.com)

Starts gazebo harmonic with the city world, then brings up the full AS2
stack for both drones (drone_cat + drone_mouse).

how the data flows for each drone:
  Gz OdometryPublisher -> ground_truth_bridge -> state_estimator -> TF tree
    -> motion_controller (pid) -> platform_gazebo -> gz cmd_vel -> simulation

to arm after launch (the motors auto-enable at t+8s):
  ros2 service call /{drone}/set_arming_state  data: true
  ros2 service call /{drone}/set_offboard_mode  data: true
  ros2 action send_goal /{drone}/TakeoffBehavior ...
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    GroupAction,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    TimerAction,
    LogInfo,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg_dir = get_package_share_directory('drone_cat_mouse_chase')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    world_file = os.path.join(pkg_dir, 'worlds', 'my_city_v3.world')
    models_dir = os.path.join(pkg_dir, 'models')
    config_dir = os.path.join(pkg_dir, 'config')


    # tell gz where our custom models are (city mesh etc)
    gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=[models_dir, ':', os.environ.get('GZ_SIM_RESOURCE_PATH', '')],
    )

    # =================== launch args ===================
    verbose_arg = DeclareLaunchArgument(
        'verbose', default_value='4',
        description='Gazebo verbosity (0-4)')
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='true')

    # =================== gazebo sim ===================
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')),
        launch_arguments={
            'gz_args': ['-r -v ', LaunchConfiguration('verbose'), ' ', world_file],
        }.items(),
    )

    # =================== clock bridge ===================
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='clock_bridge',
        output='screen',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        parameters=[{'use_sim_time': True}],
    )

    # =================== per-drone setup ===================
    drone_names = ['drone_cat', 'drone_mouse']
    world_name = 'my_city_world'

    # all drones share these config files
    platform_config     = os.path.join(config_dir, 'platform_config_file.yaml')
    control_modes       = os.path.join(config_dir, 'control_modes.yaml')
    state_est_config    = os.path.join(config_dir, 'state_estimator.yaml')
    motion_ctrl_config  = os.path.join(config_dir, 'motion_controller.yaml')
    pid_config          = os.path.join(config_dir, 'pid_speed_controller.yaml')

    all_drone_nodes = []

    for drone in drone_names:

        # ground truth bridge — this is the only localization source
        # reads gz odometry and publishes it as ROS pose+twist msgs
        gt_bridge = Node(
            package='as2_gazebo_assets',
            executable='ground_truth_bridge',
            name='ground_truth_bridge',
            namespace=drone,
            output='screen',
            parameters=[{
                'use_sim_time': True,
                'name_space': drone,
                'pose_frame_id': 'earth',
                'twist_frame_id': f'{drone}/base_link',
            }],
        )

        # ros-gz parameter bridge for each drone
        # handles cmd_vel, motor enable, imu, camera topics
        bridge_args = [
            # velocity cmd goes ROS -> GZ
            f'/model/{drone}/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            # arm/enable also ROS -> GZ
            f'/model/{drone}/velocity_controller/enable@std_msgs/msg/Bool]gz.msgs.Boolean',
            # imu comes back from GZ -> ROS (the imu sensor is nested inside the drone model)
            f'/world/{world_name}/model/{drone}/model/imu/link/internal/sensor/imu/imu'
            f'@sensor_msgs/msg/Imu[gz.msgs.IMU',
            # camera image GZ -> ROS
            f'/world/{world_name}/model/{drone}/link/base_link/sensor/camera/image'
            f'@sensor_msgs/msg/Image[gz.msgs.Image',
            # camera info GZ -> ROS
            f'/world/{world_name}/model/{drone}/link/base_link/sensor/camera/camera_info'
            f'@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
        ]
        # remap the long gz topic names to somthing AS2 expects
        bridge_remaps = [
            (f'/world/{world_name}/model/{drone}/model/imu/link/internal/sensor/imu/imu',
             f'/{drone}/sensor_measurements/imu'),
            (f'/world/{world_name}/model/{drone}/link/base_link/sensor/camera/image',
             f'/{drone}/sensor_measurements/camera/image_raw'),
            (f'/world/{world_name}/model/{drone}/link/base_link/sensor/camera/camera_info',
             f'/{drone}/sensor_measurements/camera/camera_info'),
        ]
        gz_bridge = Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name=f'{drone}_bridge',
            output='screen',
            arguments=bridge_args,
            remappings=bridge_remaps,
            parameters=[{'use_sim_time': True}],
        )

        # the full AS2 stack — platform, estimator, controller, behaviours
        as2_stack = GroupAction([
            LogInfo(msg=f'[AS2] launching stack for {drone}'),

            # platform node — translates AS2 commands into gz cmd_vel + arm msgs
            Node(
                package='as2_platform_gazebo',
                executable='as2_platform_gazebo_node',
                name='platform',
                namespace=drone,
                output='screen',
                parameters=[
                    {'use_sim_time': True},
                    {'cmd_vel_topic': f'/model/{drone}/cmd_vel'},
                    {'arm_topic': f'/model/{drone}/velocity_controller/enable'},
                    {'acro_topic': f'/gz/{drone}/acro'},
                    {'control_modes_file': control_modes},
                    platform_config,
                ],
            ),

            # state estimator — uses ground_truth plugin to read the bridge output
            # publishes the TF tree and self_localization topics
            Node(
                package='as2_state_estimator',
                executable='as2_state_estimator_node',
                name='state_estimator',
                namespace=drone,
                output='screen',
                parameters=[
                    {'use_sim_time': True},
                    {'plugin_name': 'ground_truth'},
                    {'use_gps': False},
                    {'set_origin_on_start': False},
                    {'use_gazebo_tf': False},
                    state_est_config,
                ],
            ),

            # motion controller — pid speed controller
            Node(
                package='as2_motion_controller',
                executable='as2_motion_controller_node',
                name='controller_manager',
                namespace=drone,
                output='screen',
                parameters=[
                    {'use_sim_time': True},
                    {'plugin_name': 'pid_speed_controller'},
                    motion_ctrl_config,
                    pid_config,
                ],
            ),

            # takeoff behaviour
            Node(
                package='as2_behaviors_motion',
                executable='takeoff_behavior_node',
                namespace=drone,
                output='screen',
                parameters=[
                    {'use_sim_time': True},
                    {'plugin_name': 'takeoff_plugin_speed'},
                    {'takeoff_height': 3.0},
                    {'takeoff_speed': 1.5},
                    {'takeoff_threshold': 0.2},
                    {'tf_timeout_threshold': 0.1},
                ],
            ),

            # land behaviour
            Node(
                package='as2_behaviors_motion',
                executable='land_behavior_node',
                namespace=drone,
                output='screen',
                parameters=[
                    {'use_sim_time': True},
                    {'plugin_name': 'land_plugin_speed'},
                    {'land_speed': 0.5},
                    {'land_speed_condition_percentage': 0.2},
                    {'land_condition_height': 0.2},
                    {'land_height': -10.0},
                    {'land_position_condition_time': 1.0},
                    {'tf_timeout_threshold': 0.1},
                ],
            ),

            # go-to — used for initial positioning
            Node(
                package='as2_behaviors_motion',
                executable='go_to_behavior_node',
                namespace=drone,
                output='screen',
                parameters=[
                    {'use_sim_time': True},
                    {'plugin_name': 'go_to_plugin_position'},
                    {'go_to_speed': 2.0},
                    {'go_to_threshold': 0.3},
                    {'tf_timeout_threshold': 0.1},
                ],
            ),

            # follow-reference — the cat uses this to chase the mouse
            Node(
                package='as2_behaviors_motion',
                executable='follow_reference_behavior_node',
                namespace=drone,
                output='screen',
                parameters=[
                    {'use_sim_time': True},
                    {'plugin_name': 'follow_reference_plugin_position'},
                    {'follow_reference_max_speed_x': 3.0},
                    {'follow_reference_max_speed_y': 3.0},
                    {'follow_reference_max_speed_z': 1.5},
                    {'tf_timeout_threshold': 0.1},
                ],
            ),
        ])

        all_drone_nodes.extend([gt_bridge, gz_bridge, as2_stack])

    # auto-enable the gz velocity controllers after 8s delay
    # without this the motors wont spin even if you arm through ROS
    motor_enables = [
        TimerAction(period=8.0, actions=[
            ExecuteProcess(
                cmd=['gz', 'topic', '-t',
                     f'/model/{drone}/velocity_controller/enable',
                     '-m', 'gz.msgs.Boolean', '-p', 'data: true'],
                output='screen',
            )
        ])
        for drone in drone_names
    ]

    return LaunchDescription([
        gz_resource_path,
        verbose_arg,
        use_sim_time_arg,
        gz_sim,
        clock_bridge,
    ] + all_drone_nodes + motor_enables)
