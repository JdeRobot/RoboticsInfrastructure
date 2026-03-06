#!/usr/bin/env python3
# Launch file for spawning UR5 with Robotiq gripper in Gazebo Sim (Harmonic)

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, RegisterEventHandler, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
import xacro


def generate_launch_description():
    # Get workspace directory from package share
    pkg_share_dir = get_package_share_directory("ur5_gripper_description")
    # Go up from install/ur5_gripper_description/share/ur5_gripper_description to install/
    workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(pkg_share_dir)))
    
    # Prepare environment variables for Gazebo
    gz_lib_path = os.path.join(workspace_dir, 'gz_ros2_control', 'lib')
    ur_share = os.path.join(workspace_dir, 'ur5_gripper_description', 'share')
    robotiq_share = os.path.join(workspace_dir, 'robotiq_description', 'share')
    
    gz_env = {
        'GZ_SIM_RESOURCE_PATH': f"{ur_share}:{robotiq_share}:{os.environ.get('GZ_SIM_RESOURCE_PATH', '')}",
        'GZ_SIM_SYSTEM_PLUGIN_PATH': f"{gz_lib_path}:{os.environ.get('GZ_SIM_SYSTEM_PLUGIN_PATH', '')}",
        'LD_LIBRARY_PATH': f"{gz_lib_path}:{os.environ.get('LD_LIBRARY_PATH', '')}"
    }
    # Declare arguments
    declared_arguments = []
    
    declared_arguments.append(
        DeclareLaunchArgument(
            "ur_type",
            default_value="ur5",
            description="Type/series of used UR robot.",
            choices=["ur3", "ur3e", "ur5", "ur5e", "ur10", "ur10e", "ur16e"],
        )
    )
    
    declared_arguments.append(
        DeclareLaunchArgument(
            "prefix",
            default_value='""',
            description="Prefix of the joint names",
        )
    )
    
    declared_arguments.append(
        DeclareLaunchArgument(
            "launch_rviz",
            default_value="false",
            description="Launch RViz?",
        )
    )
    
    declared_arguments.append(
        DeclareLaunchArgument(
            "gz_args",
            default_value="-r empty.sdf",
            description="Arguments for Gazebo",
        )
    )

    # Initialize Arguments
    ur_type = LaunchConfiguration("ur_type")
    prefix = LaunchConfiguration("prefix")
    launch_rviz = LaunchConfiguration("launch_rviz")
    gz_args = LaunchConfiguration("gz_args")

    # Get URDF via xacro
    xacro_file = os.path.join(
        get_package_share_directory("ur5_gripper_description"),
        "urdf",
        "ur5_robotiq85_gripper.urdf.xacro"
    )
    
    controllers_file = os.path.join(
        get_package_share_directory("ur5_gripper_description"),
        "config",
        "ur5_controllers.yaml"
    )
    
    # Process xacro directly to avoid Command() stderr issues
    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "ur_type": "ur5",
            "name": "ur",
            "prefix": "",
            "use_fake_hardware": "false",
            "sim_gazebo": "false",
            "sim_gz": "true",
            "simulation_controllers": controllers_file,
        }
    ).toxml()
    
    robot_description = {"robot_description": robot_description_content}

    # Node for robot state publisher
    node_robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[
            robot_description,
            {"use_sim_time": True}
        ],
    )

    # Gazebo Sim (Harmonic) - with environment variables
    # Create bash command that sets environment and runs Gazebo
    gz_cmd = (
        f'export GZ_SIM_SYSTEM_PLUGIN_PATH="{gz_env["GZ_SIM_SYSTEM_PLUGIN_PATH"]}" && '
        f'export GZ_SIM_RESOURCE_PATH="{gz_env["GZ_SIM_RESOURCE_PATH"]}" && '
        f'export LD_LIBRARY_PATH="{gz_env["LD_LIBRARY_PATH"]}" && '
        'gz sim -r -v 4 empty.sdf'
    )
    
    gazebo = ExecuteProcess(
        cmd=['bash', '-c', gz_cmd],
        output='screen',
        shell=False
    )

    # Spawn robot
    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic", "robot_description",
            "-name", "ur5_robotiq",
            "-allow_renaming", "true",
        ],
        output="screen",
    )

    # Bridge for clock
    gz_ros2_bridge_clock = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    # Load joint state broadcaster
    load_joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    # Load arm controller
    load_joint_trajectory_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_trajectory_controller", "-c", "/controller_manager"],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )
    
    # Load gripper controller
    load_gripper_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gripper_controller", "-c", "/controller_manager"],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    # RViz
    rviz_config_file = PathJoinSubstitution(
        [FindPackageShare("ur5_gripper_description"), "rviz", "view_robot.rviz"]
    )
    
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        condition=IfCondition(launch_rviz),
        parameters=[{"use_sim_time": True}],
    )

    # Delay controller spawner after robot spawn
    delay_joint_state_broadcaster_after_spawn = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[load_joint_state_broadcaster],
        )
    )

    delay_joint_trajectory_controller_after_joint_state_broadcaster = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=load_joint_state_broadcaster,
            on_exit=[load_joint_trajectory_controller],
        )
    )
    
    delay_gripper_controller_after_joint_trajectory = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=load_joint_trajectory_controller,
            on_exit=[load_gripper_controller],
        )
    )

    nodes = [
        gazebo,
        node_robot_state_publisher,
        spawn_entity,
        gz_ros2_bridge_clock,
        delay_joint_state_broadcaster_after_spawn,
        delay_joint_trajectory_controller_after_joint_state_broadcaster,
        delay_gripper_controller_after_joint_trajectory,
        rviz_node,
    ]

    return LaunchDescription(declared_arguments + nodes)
