import os
import xacro

from launch import LaunchDescription
from launch.actions import ExecuteProcess, RegisterEventHandler, TimerAction
from launch.event_handlers import OnProcessExit
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_share_dir = get_package_share_directory("ur5_gripper_description")
    robotiq_pkg_share_dir = get_package_share_directory("robotiq_description")

    gz_ros2_control_install = "/home/ws/install"
    gz_lib_path = os.path.join(gz_ros2_control_install, "gz_ros2_control", "lib")

    warehouse_models_path = os.path.join(robotiq_pkg_share_dir, "world", "models")
    ur5_share_parent = os.path.dirname(pkg_share_dir)
    robotiq_share_parent = os.path.dirname(robotiq_pkg_share_dir)

    resource_path = (
        ur5_share_parent + ":" +
        robotiq_share_parent + ":" +
        warehouse_models_path
    )

    gz_env = {
        "GZ_SIM_RESOURCE_PATH": resource_path,
        "GZ_SIM_SYSTEM_PLUGIN_PATH": (
            "/home/ws/install/gz_link_attacher/lib:"
            + gz_lib_path +
            ":/opt/ros/humble/lib"
        ),
        "LD_LIBRARY_PATH":
            "/home/ws/install/gz_link_attacher/lib:"
            + gz_lib_path +
            ":/opt/ros/humble/lib:/usr/lib/x86_64-linux-gnu:"
            + os.environ.get("LD_LIBRARY_PATH", ""),
        "DISPLAY": os.environ.get("DISPLAY", ":0"),
    }

    print("DEBUG: GZ_SIM_RESOURCE_PATH =", resource_path)
    xacro_file = os.path.join(
        pkg_share_dir,
        "urdf",
        "ur5_machine_vision.urdf.xacro"
    )

    controllers_file = os.path.join(pkg_share_dir, "config", "ur5_controllers.yaml")

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
        },
    ).toxml()

    robot_description = {"robot_description": robot_description_content}

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic", "robot_description",
            "-name", "ur5",
            "-allow_renaming", "true",
            "-x", "0",
            "-y", "0",
            "-z", "0.9",
            "-R", "0",
            "-P", "0",
            "-Y", "0",
        ],
        output="screen",
        additional_env=gz_env,
    )

    static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0", "0", "0.9", "0", "0", "0", "world", "base_link"],
        parameters=[{"use_sim_time": True}],
    )

    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        parameters=[{"use_sim_time": True}],
        output="screen",
    )

    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
        ],
        parameters=[{"use_sim_time": True}],
    )

    joint_trajectory_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_trajectory_controller",
            "-c", "/controller_manager",
        ],
        parameters=[{"use_sim_time": True}],
    )

    gripper_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "gripper_controller",
            "-c", "/controller_manager",
        ],
        parameters=[{"use_sim_time": True}],
    )

    delay_spawn = TimerAction(period=5.0, actions=[spawn_entity])

    delay_js = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_entity,
            on_exit=[joint_state_broadcaster],
        )
    )

    delay_traj = RegisterEventHandler(
        OnProcessExit(
            target_action=joint_state_broadcaster,
            on_exit=[joint_trajectory_controller],
        )
    )

    delay_gripper = RegisterEventHandler(
        OnProcessExit(
            target_action=joint_trajectory_controller,
            on_exit=[gripper_controller],
        )
    )

    return LaunchDescription([
        robot_state_publisher,
        static_tf,
        clock_bridge,
        delay_spawn,
        delay_js,
        delay_traj,
        delay_gripper,
    ])