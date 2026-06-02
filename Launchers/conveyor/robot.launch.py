import os
import xacro

from launch import LaunchDescription
from launch.actions import SetEnvironmentVariable
from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    # ==================================================
    # ENVIRONMENT VARIABLES FOR GAZEBO / GZ
    # ==================================================

    gz_ros2_control_path = "/home/ws/install/gz_ros2_control/lib"
    gz_link_attacher_path = "/home/ws/install/gz_link_attacher/lib"

    gz_plugin_path = (
        gz_link_attacher_path
        + ":"
        + gz_ros2_control_path
        + ":"
        + "/opt/ros/humble/lib"
    )

    resource_path = (
        os.path.dirname(
            get_package_share_directory("ros2srrc_ur3_gazebo")
        )
    )

    set_resource_path = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=resource_path,
    )

    set_gz_plugin_path = SetEnvironmentVariable(
        name="GZ_SIM_SYSTEM_PLUGIN_PATH",
        value=gz_plugin_path,
    )

    existing_ld = os.environ.get("LD_LIBRARY_PATH", "")

    set_ld_library_path = SetEnvironmentVariable(
        name="LD_LIBRARY_PATH",
        value=gz_plugin_path
        + ":/usr/lib/x86_64-linux-gnu:"
        + existing_ld,
    )

    # ==================================================
    # ROBOT DESCRIPTION
    # ==================================================

    xacro_file = os.path.join(
        get_package_share_directory("ros2srrc_ur3_gazebo"),
        "urdf",
        "ur3_robotiq_2f85.urdf.xacro",
    )

    robot_description = {
        "robot_description": xacro.process_file(
            xacro_file,
            mappings={
                "bringup": "false",
                "hmi": "false",
                "robot_ip": "0.0.0.0",
                "EE": "false",
                "EE_name": "none",
                "script_filename": "none",
                "input_recipe_filename": "none",
                "output_recipe_filename": "none",
            },
        ).toxml()
    }

    # ==================================================
    # ROBOT STATE PUBLISHER
    # ==================================================

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[
            robot_description,
            {"use_sim_time": True},
        ],
    )

    # ==================================================
    # SPAWN ROBOT
    # ==================================================

    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-topic",
            "robot_description",
            "-name",
            "ur3",
            "-x",
            "0",
            "-y",
            "0",
            "-z",
            "1.0",
        ],
    )

    # ==================================================
    # LAUNCH
    # ==================================================

    return LaunchDescription([
        set_gz_plugin_path,
        set_ld_library_path,
        set_resource_path,

        robot_state_publisher,
        spawn_robot,
    ])