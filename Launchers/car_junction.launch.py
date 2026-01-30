Car Junction exercise launch file.
Updated for Gazebo Harmonic compatibility.
Verified working on Docker environment.
"""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    package_dir = get_package_share_directory("custom_robots")
    ros_gz_sim = get_package_share_directory("ros_gz_sim")
    use_sim_time = LaunchConfiguration("use_sim_time", default="true")
    world_file_name = "road_junction.world"
    # Use world from the mounted source
    worlds_dir = "/home/ws/src/RoboticsInfrastructure/Worlds"
    if not os.path.exists(worlds_dir):
        worlds_dir = "/opt/jderobot/Worlds"
    world_path = os.path.join(worlds_dir, world_file_name)

    # Model paths for Gazebo Harmonic
    gazebo_models_path = os.path.join(package_dir, "models")
    # Check both common locations for CustomRobots
    car_junction_models = "/opt/jderobot/CustomRobots/car_junction/models"
    if not os.path.exists(car_junction_models):
        car_junction_models = "/home/ws/src/CustomRobots/car_junction/models"
    
    # Build resource path with all model directories
    existing_path = os.environ.get("GZ_SIM_RESOURCE_PATH", "")
    additional_paths = [gazebo_models_path, car_junction_models, worlds_dir, "/resources"]
    
    # Filter only existing paths to avoid noise
    valid_additional = [p for p in additional_paths if os.path.exists(p)]
    
    resource_paths = [existing_path] + valid_additional if existing_path else valid_additional
    
    set_gz_resource_path = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=":".join(resource_paths),
    )

    # Gazebo server (headless simulation)
    gazebo_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": f"-r -s -v4 {world_path}",
            "on_exit_shutdown": "true",
        }.items(),
    )

    # Gazebo GUI client
    gazebo_client = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": "-g -v4",
            "on_exit_shutdown": "true",
        }.items(),
    )

    declare_use_simulator_cmd = DeclareLaunchArgument(
        name="use_simulator",
        default_value="True",
        description="Whether to start the simulator",
    )

    # ROS-Gazebo bridge for Harmonic
    start_ros_gazebo_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
            "/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",
            "/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry",
            "/waymo/lidar/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked",
            "/waymo/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",
        ],
        parameters=[{"use_sim_time": True}],
        output="screen",
    )

    start_ros_gazebo_image_bridge = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["/waymo/camera_front"],
        output="screen",
    )

    # Create the launch description and populate
    ld = LaunchDescription()
    ld.add_action(set_gz_resource_path)
    ld.add_action(declare_use_simulator_cmd)
    ld.add_action(gazebo_server)
    ld.add_action(gazebo_client)
    ld.add_action(start_ros_gazebo_bridge)
    ld.add_action(start_ros_gazebo_image_bridge)

    return ld
