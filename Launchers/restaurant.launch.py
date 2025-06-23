import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PythonExpression
from launch_ros.actions import SetRemap
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    # Set the path to the Nav2 package
    pkg_nav2_ros = FindPackageShare(package="nav2_bringup").find("nav2_bringup")

    # Set the path to the Yolo package
    pkg_yolo_ros = FindPackageShare(package="darknet_ros").find("darknet_ros")

    # Set the path to the Gazebo ROS package
    pkg_gazebo_ros = FindPackageShare(package="gazebo_ros").find("gazebo_ros")

    # Set the path to this package.
    pkg_share = FindPackageShare(package="custom_robots").find("custom_robots")

    # Set the path to the world file
    world_file_name = "restaurant.world"
    worlds_dir = "/opt/jderobot/Worlds"
    world_path = os.path.join(worlds_dir, world_file_name)

    # Set the path to the SDF model files.
    gazebo_models_path = os.path.join(pkg_share, "models")
    os.environ["GAZEBO_MODEL_PATH"] = (
        f"{os.environ.get('GAZEBO_MODEL_PATH', '')}:{':'.join(gazebo_models_path)}"
    )

    ########### YOU DO NOT NEED TO CHANGE ANYTHING BELOW THIS LINE ##############
    # Launch configuration variables specific to simulation
    headless = LaunchConfiguration("headless")
    use_sim_time = LaunchConfiguration("use_sim_time")
    use_simulator = LaunchConfiguration("use_simulator")
    world = LaunchConfiguration("world")
    slam = LaunchConfiguration("slam")
    map_file = LaunchConfiguration("map")
    params_file = LaunchConfiguration("params_file")

    declare_simulator_cmd = DeclareLaunchArgument(
        name="headless",
        default_value="False",
        description="Whether to execute gzclient",
    )

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        name="use_sim_time",
        default_value="true",
        description="Use simulation (Gazebo) clock if true",
    )

    declare_use_simulator_cmd = DeclareLaunchArgument(
        name="use_simulator",
        default_value="True",
        description="Whether to start the simulator",
    )

    declare_world_cmd = DeclareLaunchArgument(
        name="world",
        default_value=world_path,
        description="Full path to the world model file to load",
    )

    declare_slam_cmd = DeclareLaunchArgument("slam", default_value="True")

    declare_map_cmd = DeclareLaunchArgument(
        "map",
        default_value=os.path.join(
            gazebo_models_path, "restaurant", "maps", "restaurant.yaml"
        ),
    )

    declare_nav_params_cmd = DeclareLaunchArgument(
        "params_file",
        default_value=os.path.join(
            gazebo_models_path, "restaurant", "params", "roomba_sim_nav_params.yaml"
        ),
    )

    # Specify the actions

    # Start Yolo v4
    start_yolo_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_yolo_ros, "launch", "darknet_ros.launch.py")
        )
    )

    # Start Gazebo server
    start_gazebo_server_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, "launch", "gzserver.launch.py")
        ),
        condition=IfCondition(use_simulator),
        launch_arguments={"world": world}.items(),
    )

    localization_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav2_ros, "launch", "localization_launch.py")
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "map": map_file,
            "slam": slam,
            "params_file": params_file,
        }.items(),
    )

    navigation_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav2_ros, "launch", "navigation_launch.py")
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "params_file": params_file,
        }.items(),
    )

    # Create the launch description and populate
    ld = LaunchDescription()

    # Declare the launch options
    ld.add_action(declare_simulator_cmd)
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_use_simulator_cmd)
    ld.add_action(declare_world_cmd)
    ld.add_action(declare_slam_cmd)
    ld.add_action(declare_map_cmd)
    ld.add_action(declare_nav_params_cmd)

    # Add any actions
    ld.add_action(start_gazebo_server_cmd)
    ld.add_action(start_yolo_cmd)
    ld.add_action(localization_cmd)
    ld.add_action(navigation_cmd)

    # Remap nav2
    cmd_vel_remap = SetRemap(src="cmd_vel_nav", dst="cmd_vel")
    ld.add_action(cmd_vel_remap)

    return ld
