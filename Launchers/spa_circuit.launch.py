import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():

    # Aquí el paquete correcto para gazebo_ros
    pkg_gazebo_ros = FindPackageShare(package='gazebo_launch').find('gazebo_launch')

    # Ruta a tu carpeta de modelos en tu workspace (ajusta si es necesario)
    # Si tus modelos están en ~/gzROS/src/gazebo_launch/worlds/models o similar, pon esa ruta:
    pkg_share = os.path.expanduser('~/gzROS/src/gazebo_launch/models')

    # Nombre del archivo del mundo
    world_file_name = 'spa_circuit.world'
    world_path = os.path.join(pkg_share, world_file_name)

    # Añadir el path de modelos a la variable de entorno GAZEBO_MODEL_PATH
    os.environ["GAZEBO_MODEL_PATH"] = f"{os.environ.get('GAZEBO_MODEL_PATH', '')}:{pkg_share}"

    # Configuraciones de lanzamiento
    headless = LaunchConfiguration('headless')
    use_sim_time = LaunchConfiguration('use_sim_time')
    use_simulator = LaunchConfiguration('use_simulator')
    world = LaunchConfiguration('world')

    declare_simulator_cmd = DeclareLaunchArgument(
        name='headless',
        default_value='False',
        description='Whether to execute gzclient'
    )

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        name='use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )

    declare_use_simulator_cmd = DeclareLaunchArgument(
        name='use_simulator',
        default_value='True',
        description='Whether to start the simulator'
    )

    declare_world_cmd = DeclareLaunchArgument(
        name='world',
        default_value=world_path,
        description='Full path to the world model file to load'
    )

    # Lanzar el servidor de Gazebo
    start_gazebo_server_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')),
        condition=IfCondition(use_simulator),
        launch_arguments={'world': world}.items()
    )

    ld = LaunchDescription()

    ld.add_action(declare_simulator_cmd)
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_use_simulator_cmd)
    ld.add_action(declare_world_cmd)

    ld.add_action(start_gazebo_server_cmd)

    return ld
