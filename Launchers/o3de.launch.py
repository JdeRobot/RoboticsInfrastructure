import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():

    ProjectName = "ROS2O3DE"
    SimulatorPath="/data/workspace/"+ProjectName+"/build/linux/bin/profile/"+ProjectName+".GameLauncher"

    declare_simulator_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(SimulatorPath)
        ),
    )

    Level = "DemoLevel"

    declare_world_cmd = DeclareLaunchArgument(
        name='LoadLevel',
        value=Level,
    )

    ld = LaunchDescription()

    # Declare the launch options
    ld.add_action(declare_simulator_cmd)
    ld.add_action(declare_world_cmd)

    return ld