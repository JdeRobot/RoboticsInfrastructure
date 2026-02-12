import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
import yaml
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    shared_dir = FindPackageShare(package="custom_robots").find("custom_robots")

    params_file = os.path.join(shared_dir, "config", "kobuki_node_params.yaml")
    with open(params_file, "r") as f:
        kobuki_params = yaml.safe_load(f)["kobuki_ros_node"]["ros__parameters"]

    kobuki_cmd = Node(
        package="kobuki_node",
        executable="kobuki_ros_node",
        output="screen",
        parameters=[kobuki_params],
    )

    ld = LaunchDescription()

    ld.add_action(kobuki_cmd)

    return ld
