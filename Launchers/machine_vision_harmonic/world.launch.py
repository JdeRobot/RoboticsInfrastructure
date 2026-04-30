import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    world_path = "/opt/jderobot/Worlds/machine_vision_harmonic.world"

    # =========================
    # PATHS
    # =========================

    gz_ros2_control_path = "/home/ws/install/gz_ros2_control/lib"
    gz_plugin_path = gz_ros2_control_path + ":" + "/opt/ros/humble/lib"

    custom_models_path = "/home/dev_ws/src/IndustrialRobots/ros2_SimRealRobotControl/packages/ur5/ros2srrc_ur5_gazebo/models"

    resource_path = (
        os.path.dirname(get_package_share_directory("ur5_gripper_description"))
        + ":"
        + os.path.dirname(get_package_share_directory("robotiq_description"))
        + ":"
        + os.path.join(
            get_package_share_directory("robotiq_description"), "world", "models"
        )
        + ":"
        + custom_models_path
    )

    # =========================
    # ENV VARS
    # =========================

    set_resource_path = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH", value=resource_path
    )

    set_plugin_path = SetEnvironmentVariable(
        name="GZ_SIM_SYSTEM_PLUGIN_PATH", value=gz_plugin_path
    )

    existing_ld = os.environ.get("LD_LIBRARY_PATH", "")

    set_ld_library_path = SetEnvironmentVariable(
        name="LD_LIBRARY_PATH",
        value=gz_plugin_path + ":/usr/lib/x86_64-linux-gnu:" + existing_ld,
    )

    # =========================
    # GAZEBO
    # =========================

    gz = ExecuteProcess(
        cmd=["gz", "sim", "-r", "-s", "-v", "4", world_path],
        output="screen",
    )

    return LaunchDescription(
        [set_plugin_path, set_ld_library_path, set_resource_path, gz]
    )