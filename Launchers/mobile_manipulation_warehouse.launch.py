import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    AppendEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    ros_gz_sim = get_package_share_directory("ros_gz_sim")
    package_dir = get_package_share_directory("custom_robots")

    world_file_name = "mobile_manipulation_warehouse.world"
    worlds_dir = "/opt/jderobot/Scenes"
    world_path = os.path.join(worlds_dir, world_file_name)

    # The Robotiq gripper meshes use package:// URIs
    robotiq_resource_path = AppendEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=os.path.dirname(get_package_share_directory("robotiq_description")),
    )

    gazebo_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": ["-s -v4 ", world_path],
            "on_exit_shutdown": "true",
        }.items(),
    )

    world_entity_cmd = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-name", "world", "-file", world_path],
        output="screen",
    )

    gz_ros2_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
        ],
        output="screen",
    )

    pkg_nav2_ros = FindPackageShare(package="nav2_bringup").find("nav2_bringup")

    params_file = os.path.join(
        package_dir,
        "models",
        "mmo500",
        "params",
        "nav2_config.yaml",
    )

    localization_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav2_ros, "launch", "localization_launch.py")
        ),
        launch_arguments={
            "use_sim_time": "True",
            "map": os.path.join("/resources", "exercises", "mobile_manipulation/maps/map.yaml"),
            "slam": "True",
            "params_file": params_file,
        }.items(),
    )

    navigation_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav2_ros, "launch", "navigation_launch.py")
        ),
        launch_arguments={
            "use_sim_time": "true",
            "params_file": params_file,
        }.items(),
    )

    ld = LaunchDescription()
    ld.add_action(robotiq_resource_path)
    ld.add_action(gazebo_server)
    ld.add_action(world_entity_cmd)
    ld.add_action(gz_ros2_bridge)
    ld.add_action(localization_cmd)
    ld.add_action(navigation_cmd)

    return ld
