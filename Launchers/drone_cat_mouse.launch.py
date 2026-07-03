"""Entry point for the Drone Cat-Mouse exercise."""

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
    bridges_path = os.path.join(custom_robots_share, "bridges", "drone_cat_mouse.yaml")

    world_file_name = "drone_cat_mouse_city.world"
    worlds_dir = "/opt/jderobot/Worlds"
    world_path = os.path.join(worlds_dir, world_file_name)

    jderobot_drones_launch = os.path.join(
        get_package_share_directory("jderobot_drones"), "launch"
    )

    declare_use_simulator_cmd = DeclareLaunchArgument(
        name="use_simulator",
        default_value="True",
        description="Whether to start the simulator",
    )

    # gazebo + the ros_gz bridges. the one bridges file covers both drones.
    gzsim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([jderobot_drones_launch, "/gz_sim.launch.py"]),
        condition=IfCondition(LaunchConfiguration("use_simulator")),
        launch_arguments={
            "namespace": "drone0",
            "bridges_file": bridges_path,
            "world_file": world_path,
        }.items(),
    )

    # the aerostack2 stack for drone0 (the cat)
    as2_drone0 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [jderobot_drones_launch, "/as2_default_gazebo_sim.launch.py"]
        ),
        launch_arguments={"namespace": "drone0"}.items(),
    )

    # same thing again for drone1 (the mouse) - the only difference is the
    # namespace, the topics get worked out from it inside that launch file
    as2_drone1 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [jderobot_drones_launch, "/as2_default_gazebo_sim.launch.py"]
        ),
        launch_arguments={"namespace": "drone1"}.items(),
    )

    # camera image bridges for drone0
    drone0_frontal_bridge = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["/drone0/frontal_cam/image_raw"],
        output="screen",
    )
    drone0_ventral_bridge = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["/drone0/ventral_cam/image_raw"],
        output="screen",
    )

    # gz_sim.launch.py only sets up a ground_truth bridge for drone0, so we
    # add drone1's here by hand - without it drone1 has no position feedback
    drone1_ground_truth_bridge = Node(
        package="as2_gazebo_assets",
        executable="ground_truth_bridge",
        namespace="drone1",
        output="screen",
        parameters=[
            {
                "use_sim_time": True,
                "name_space": "drone1",
                "pose_frame_id": "earth",
                "twist_frame_id": "drone1/base_link",
            },
        ],
    )

    # camera image bridges for drone1
    drone1_frontal_bridge = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["/drone1/frontal_cam/image_raw"],
        output="screen",
    )
    drone1_ventral_bridge = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["/drone1/ventral_cam/image_raw"],
        output="screen",
    )

    ld = LaunchDescription()
    ld.add_action(declare_use_simulator_cmd)
    ld.add_action(gzsim)
    ld.add_action(as2_drone0)
    ld.add_action(as2_drone1)
    ld.add_action(drone1_ground_truth_bridge)
    ld.add_action(drone0_frontal_bridge)
    ld.add_action(drone0_ventral_bridge)
    ld.add_action(drone1_frontal_bridge)
    ld.add_action(drone1_ventral_bridge)

    return ld
