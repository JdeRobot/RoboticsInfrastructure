from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable, AppendEnvironmentVariable
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    # 🔹 Ruta al mundo
    world_path = "/home/ws/Worlds/conveyor_world.world"

    # 🔹 IMPORTANTE: rutas de modelos
    models_path = "/home/ws/CustomRobots"

    # 🔹 (opcional pero recomendable)
    gz_ros2_control_install = "/home/ws/install"
    gz_lib_path = os.path.join(gz_ros2_control_install, "gz_ros2_control", "lib")

    # 🔹 ENV correcto (esto es la clave)
    gz_env = {
        "GZ_SIM_RESOURCE_PATH": models_path,
        "GZ_SIM_SYSTEM_PLUGIN_PATH": gz_lib_path + ":/opt/ros/humble/lib",
        "LD_LIBRARY_PATH": gz_lib_path + ":/opt/ros/humble/lib:/usr/lib/x86_64-linux-gnu",
        "DISPLAY": ":2",
    }

    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-s", "-r", "-v", "4", world_path],
        output="screen",
        additional_env=gz_env,
        shell=False,
    )

    ld = LaunchDescription()

    # 🔥 MUY IMPORTANTE (esto te faltaba)
    ld.add_action(
        SetEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH",
            models_path
        )
    )

    ld.add_action(
        AppendEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH",
            models_path
        )
    )

    ld.add_action(gazebo)

    return ld