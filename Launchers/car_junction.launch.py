"""
car_junction.launch.py

Entry point for the Car Junction exercise.
"""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():

    custom_robots_share = get_package_share_directory("custom_robots")
    ros_gz_sim = get_package_share_directory("ros_gz_sim")
    world_path = os.path.join(
        custom_robots_share, "worlds", "road_junction.world"
    )

    declare_use_simulator_cmd = DeclareLaunchArgument(
        name="use_simulator",
        default_value="True",
        description="Whether to start the simulator",
    )
    gzsim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(get_package_share_directory("jderobot_drones"), "launch"),
                "/gz_sim.launch.py",
            ]
        ),
        condition=IfCondition(LaunchConfiguration("use_simulator")),
        launch_arguments={
            "namespace": "drone0",
            "bridges_file": bridges_path,
            "world_file": world_path,
        }.items(),
    )

    as2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(get_package_share_directory("jderobot_drones"), "launch"),
                "/as2_default_gazebo_sim.launch.py",
            ]
        ),
        launch_arguments={
            "namespace": "drone0",
        }.items(),
    )

    start_ros_gazebo_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
            "/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist", 
            "/odom@nav_msgs/msg/Odometry]gz.msgs.Odometry",
            "/waymo/lidar/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked",
            "/waymo/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",
        ],
        parameters=[{'use_sim_time': True}],
        output="screen",
    )
    
    start_ros_gazebo_image_bridge = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["/waymo/camera_front@sensor_msgs/msg/Image[gz.msgs.Image"],
        output="screen",
    )

    start_gazebo_frontal_image_bridge_cmd = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["/drone0/frontal_cam/image_raw"],
        output="screen",
    )

    start_gazebo_ventral_image_bridge_cmd = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["/drone0/ventral_cam/image_raw"],
        output="screen",
    )
    # Create the launch description and populate
    ld = LaunchDescription()
    ld.add_action(declare_use_simulator_cmd)
    ld.add_action(gzsim)
    ld.add_action(as2)
    ld.add_action(start_gazebo_frontal_image_bridge_cmd)
    ld.add_action(start_gazebo_ventral_image_bridge_cmd)
    ld.add_action(start_ros_gazebo_bridge)
    ld.add_action(start_ros_gazebo_image_bridge)

    return ld
