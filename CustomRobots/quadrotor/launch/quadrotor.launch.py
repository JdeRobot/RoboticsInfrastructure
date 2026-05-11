import os
import xacro

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration, Command, IfElseSubstitution
from launch.actions import DeclareLaunchArgument, OpaqueFunction, IncludeLaunchDescription
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch.launch_description_sources import PythonLaunchDescriptionSource

def launch_setup(context):
    use_sim_time = LaunchConfiguration("use_sim_time")
    x = LaunchConfiguration("x")
    y = LaunchConfiguration("y")
    z = LaunchConfiguration("z")
    R = LaunchConfiguration("R")
    P = LaunchConfiguration("P")
    Y = LaunchConfiguration("Y")
    gz_sensor = LaunchConfiguration("sensor")
    gz_namespace = LaunchConfiguration("namespace")
    namespace = gz_namespace.perform(context)

    package_dir = get_package_share_directory("custom_robots")

    nodes_to_start = []

    sensor = gz_sensor.perform(context)

    bridge_yaml = os.path.join(package_dir, "params", f"quadrotor_{sensor}.yaml")

    # =========================
    # ROBOT DESCRIPTION (URDF)
    # =========================
    xacro_file = os.path.join(
        package_dir,
        "models",
        "quadrotor",
        "quadrotor.urdf.xacro",
    )

    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "camera": "true" if sensor == "camera" else "false",
            "namespace": namespace,
        },
    ).toxml()

    robot_description = {"robot_description": robot_description_content}

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic",
            namespace + "/robot_description",
            "-name",
            "quadrotor",
            "-allow_renaming",
            "true",
            "-x",
            x,
            "-y",
            y,
            "-z",
            z,
            "-R",
            R,
            "-P",
            P,
            "-Y",
            Y,
        ],
        output="screen",
    )

    gz_ros2_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        namespace=namespace,
        parameters=[{"config_file": bridge_yaml}],
        output="screen",
    )

    as2_gt_bridge = Node(
        package="as2_gazebo_assets",
        executable="ground_truth_bridge",
        namespace=namespace,
        output="screen",
        parameters=[
            {
                "name_space": namespace,
                "pose_frame_id": "earth",
                "twist_frame_id": [namespace,"/base_link"],
            },
        ],
    )

    as2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(get_package_share_directory("jderobot_drones"), "launch"),
                "/as2_default_gazebo_sim.launch.py",
            ]
        ),
        launch_arguments={
            "namespace": namespace,
        }.items(),
    )

    nodes_to_start.append(robot_state_publisher_node)
    nodes_to_start.append(gz_spawn_entity)
    nodes_to_start.append(gz_ros2_bridge)
    nodes_to_start.append(as2_gt_bridge)
    nodes_to_start.append(as2)

    # Sensor deppending on sensor arguments
    if sensor == "camera":
        gz_ros2_frontal_image_bridge = Node(
            package="ros_gz_image",
            executable="image_bridge",
            arguments=[f"/{namespace}/frontal_cam/image_raw"],
            output="screen",
        )

        gz_ros2_ventral_image_bridge = Node(
            package="ros_gz_image",
            executable="image_bridge",
            arguments=[f"/{namespace}/ventral_cam/image_raw"],
            output="screen",
        )

        nodes_to_start.append(gz_ros2_frontal_image_bridge)
        nodes_to_start.append(gz_ros2_ventral_image_bridge)

    return nodes_to_start


def generate_launch_description():
    declared_arguments = []

    # Add any entry parameter
    declared_arguments.append(
        DeclareLaunchArgument("use_sim_time", default_value="true")
    )
    declared_arguments.append(DeclareLaunchArgument("x", default_value="0"))
    declared_arguments.append(DeclareLaunchArgument("y", default_value="0"))
    declared_arguments.append(DeclareLaunchArgument("z", default_value="0"))
    declared_arguments.append(DeclareLaunchArgument("R", default_value="0"))
    declared_arguments.append(DeclareLaunchArgument("P", default_value="0"))
    declared_arguments.append(DeclareLaunchArgument("Y", default_value="0"))
    declared_arguments.append(DeclareLaunchArgument("sensor", default_value="camera"))
    declared_arguments.append(DeclareLaunchArgument("namespace", description="Namespace to use", default_value="drone0"))

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
