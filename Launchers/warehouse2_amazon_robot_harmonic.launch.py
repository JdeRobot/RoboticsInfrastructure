import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable, AppendEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():

    package_dir = get_package_share_directory("custom_robots")
    ros_gz_sim = get_package_share_directory("ros_gz_sim")

    gazebo_models_path = os.path.join(package_dir, "models")

    robot_launch_dir = "/opt/jderobot/Launchers/amazon_robot_harmonic"
    gui_config_path = "/opt/jderobot/Launchers/visualization/amazon_robot_harmonic.config"

    x_pose = LaunchConfiguration("x_pose", default="0.0")
    y_pose = LaunchConfiguration("y_pose", default="0.0")
    z_pose = LaunchConfiguration("z_pose", default="0.5")

    world_path = os.path.join("/opt/jderobot/Worlds", "warehouse2_harmonic.world")

    gazebo_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(ros_gz_sim, "launch", "gz_sim.launch.py")),
        launch_arguments={
            "gz_args": [f"-r -s -v4 --gui-config {gui_config_path} {world_path}"],
            "on_exit_shutdown": "true",
        }.items(),
    )

    spawn_robot_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(robot_launch_dir, "spawn_robot.launch.py")),
        launch_arguments={"x_pose": x_pose, "y_pose": y_pose, "z_pose": z_pose}.items(),
    )

    ld = LaunchDescription()
    ld.add_action(SetEnvironmentVariable("HAL_MODULE", "HAL2"))
    ld.add_action(SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", gazebo_models_path))
    ld.add_action(AppendEnvironmentVariable("GZ_SIM_RESOURCE_PATH", gazebo_models_path))
    ld.add_action(gazebo_server)
    ld.add_action(spawn_robot_cmd)
    return ld