import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    AppendEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    # Rutas a directorios
    package_dir = get_package_share_directory("custom_robots") 
    ros_gz_sim = get_package_share_directory("ros_gz_sim")

    gazebo_models_path = os.path.join(package_dir, "models")

    # Directorio de los launchers específicos del robot (para robot_state_publisher)
    robot_launch_dir = "/opt/jderobot/Launchers/autopark_line" 

    use_sim_time = LaunchConfiguration("use_sim_time", default="true")

    
    # Nombre y ruta del mundo
    world_file_name = "autopark_line.world" 
    worlds_dir = "/opt/jderobot/Worlds" 
    world_path = os.path.join(worlds_dir, world_file_name)

    # Iniciar el servidor de Gazebo/Ignition y cargar el mundo
    gazebo_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": ["-r -s -v4 ", world_path], 
            "on_exit_shutdown": "true",
        }.items(),
    )

    # Lanzar el robot_state_publisher (Necesario para las transformaciones del robot)
    robot_state_publisher_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(robot_launch_dir, "robot_state_publisher.launch.py")
        ),
        launch_arguments={"use_sim_time": use_sim_time}.items(),
    )

    # Configuración de LaunchDescription
    ld = LaunchDescription()

    # Variables de entorno
    ld.add_action(SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", gazebo_models_path))
    set_env_vars_resources = AppendEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH", os.path.join(package_dir, "models")
    )
    ld.add_action(set_env_vars_resources)
    
    # Servidor de simulación
    ld.add_action(gazebo_server)
    
    
    # Componentes del robot
    ld.add_action(robot_state_publisher_cmd)

    return ld