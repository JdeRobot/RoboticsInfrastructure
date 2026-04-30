import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    package_dir = get_package_share_directory("custom_robots")
    robotiq_description_pkg = get_package_share_directory("robotiq_description")
    ur5_gripper_pkg = get_package_share_directory("ur5_gripper_description")

    warehouse_models_path = os.path.join(robotiq_description_pkg, "world", "models")

    ur5_share_parent = os.path.dirname(ur5_gripper_pkg)
    robotiq_share_parent = os.path.dirname(robotiq_description_pkg)

    # =========================
    # PATHS
    # =========================

    world_path = "/opt/jderobot/Worlds/machine_vision_harmonic.world"   

    gz_lib_path = "/home/ws/install/gz_ros2_control/lib"

    resource_path = (
        ur5_share_parent + ":" +
        robotiq_share_parent + ":" +
        warehouse_models_path
    )

    gz_env = {
            "GZ_SIM_RESOURCE_PATH": resource_path,
            "GZ_SIM_SYSTEM_PLUGIN_PATH": (
                "/usr/lib/x86_64-linux-gnu/gz-sim-8/plugins:"
                "/usr/lib/x86_64-linux-gnu/gz-sim-8/systems:"
                + gz_lib_path +
                ":/opt/ros/humble/lib"
            ),
            "LD_LIBRARY_PATH": (
                gz_lib_path +
                ":/opt/ros/humble/lib:/usr/lib/x86_64-linux-gnu"
            ),
        }
    
    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-s", "-r", "-v", "4", world_path],
        output="screen",
        additional_env=gz_env,
    )

    return LaunchDescription([gazebo])