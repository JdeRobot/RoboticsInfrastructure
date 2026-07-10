"""Launch file for Aerostack2 default Gazebo simulation."""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, SetParameter


def _launch_setup(context, *args, **kwargs):
    """work out the gz topics for this drone and start its nodes."""
    as2_sim_config = os.path.join(
        get_package_share_directory("jderobot_drones"),
        "sim_config/gzsim/as2_config.yaml",
    )

    namespace = LaunchConfiguration("namespace").perform(context)

    # if the caller passed a topic use it, otherwise build /gz/<namespace>/...
    #
    # heads up - we hand these topics straight into the Node as plain strings,
    # NOT through LaunchConfiguration. the upstream platform_gazebo_launch.py
    # declares cmd_vel_topic/arm_topic/acro_topic with DeclareLaunchArgument and
    # reads them back with LaunchConfiguration. the catch is every launch file
    # shares one global context, and DeclareLaunchArgument only sets a value if
    # it isn't already there. so with two drones, drone0 registers its topics
    # first and drone1 just inherits drone0's - both ended up driving
    # /gz/drone0/cmd_vel and the second drone never moved. easiest way out is to
    # skip that file and start the node ourselves with the real topic strings.
    cmd_vel = (
        LaunchConfiguration("cmd_vel_topic").perform(context)
        or f"/gz/{namespace}/cmd_vel"
    )
    arm = LaunchConfiguration("arm_topic").perform(context) or f"/gz/{namespace}/arm"
    acro = LaunchConfiguration("acro_topic").perform(context) or f"/gz/{namespace}/acro"

    control_modes = os.path.join(
        get_package_share_directory("as2_platform_gazebo"),
        "config",
        "control_modes.yaml",
    )
    platform_gazebo = Node(
        package="as2_platform_gazebo",
        executable="as2_platform_gazebo_node",
        name="platform",
        namespace=namespace,
        output="screen",
        emulate_tty=True,
        parameters=[
            {
                "use_sim_time": True,
                "control_modes_file": control_modes,
                "cmd_vel_topic": cmd_vel,
                "arm_topic": arm,
                "acro_topic": acro,
            },
            as2_sim_config,
        ],
    )

    state_estimator = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory("as2_state_estimator"), "launch"
                ),
                "/ground_truth_state_estimator.launch.py",
            ]
        ),
        launch_arguments={
            "namespace": namespace,
            "config_file": as2_sim_config,
            "use_sim_time": "true",
        }.items(),
    )

    motion_controller = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory("as2_motion_controller"), "launch"
                ),
                "/controller_launch.py",
            ]
        ),
        launch_arguments={
            "namespace": namespace,
            "plugin_name": "pid_speed_controller",
            "config_file": as2_sim_config,
            "use_sim_time": "true",
        }.items(),
    )

    return [platform_gazebo, state_estimator, motion_controller]


def generate_launch_description():
    """start the aerostack2 nodes."""
    return LaunchDescription(
        [
            # the state_estimator and motion_controller launch files default
            # use_sim_time to False. when that happens the controller asks for
            # transforms at the real wall-clock time while the sim is publishing
            # them at sim time, so it complains about looking "into the future",
            # the twist never gets converted, and the drone just sits on the
            # ground. so force sim time on for everything we start here.
            SetParameter(name="use_sim_time", value=True),
            DeclareLaunchArgument(
                "namespace", default_value="drone0", description="Drone namespace."
            ),
            DeclareLaunchArgument(
                "cmd_vel_topic",
                default_value="",
                description="Gazebo cmd_vel topic. Empty = auto-derive from namespace.",
            ),
            DeclareLaunchArgument(
                "arm_topic",
                default_value="",
                description="Gazebo arm topic. Empty = auto-derive from namespace.",
            ),
            DeclareLaunchArgument(
                "acro_topic",
                default_value="",
                description="Gazebo acro topic. Empty = auto-derive from namespace.",
            ),
            OpaqueFunction(function=_launch_setup),
        ]
    )
