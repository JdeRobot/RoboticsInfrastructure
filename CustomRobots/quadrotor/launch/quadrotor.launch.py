import os
import xacro

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration, Command, IfElseSubstitution
from launch.actions import (
    DeclareLaunchArgument,
    OpaqueFunction,
    IncludeLaunchDescription,
)
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
    gz_entity = LaunchConfiguration("entity")

    package_dir = get_package_share_directory("custom_robots")

    nodes_to_start = []

    sensor = gz_sensor.perform(context)
    namespace = gz_namespace.perform(context)
    entity = gz_entity.perform(context)

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
        namespace=gz_namespace,
        output="screen",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        namespace=gz_namespace,
        arguments=[
            "-topic",
            "robot_description",
            "-name",
            entity,
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
        namespace=gz_namespace,
        arguments=[
            f"/model/{namespace}/pose@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V",
            f"/model/{namespace}/pose_static@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V",
            f"/model/{namespace}/imu@sensor_msgs/msg/Imu[gz.msgs.IMU",
            f"/model/{namespace}/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",
            f"/model/{namespace}/velocity_controller/enable@std_msgs/msg/Bool]gz.msgs.Boolean",
        ],
        remappings=[
            (f"/model/{namespace}/cmd_vel", f"/gz/{namespace}/cmd_vel"),
            (f"/model/{namespace}/velocity_controller/enable", f"/gz/{namespace}/arm"),
            (f"/model/{namespace}/pose", "/tf"),
            (f"/model/{namespace}/pose_static", "/tf"),
            (f"/model/{namespace}/imu", f"/gz/{namespace}/imu"),
        ],
        output="screen",
    )

    as2_gt_bridge = Node(
        package="as2_gazebo_assets",
        executable="ground_truth_bridge",
        namespace=gz_namespace,
        output="screen",
        parameters=[
            {
                "name_space": namespace,
                "pose_frame_id": "earth",
                "twist_frame_id": f"{namespace}/base_link",
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
        launch_arguments={"namespace": gz_namespace}.items(),
    )

    nodes_to_start.append(gz_spawn_entity)
    nodes_to_start.append(gz_ros2_bridge)
    nodes_to_start.append(as2_gt_bridge)
    nodes_to_start.append(as2)
    nodes_to_start.append(robot_state_publisher_node)

    # Sensor deppending on sensor arguments
    if sensor == "camera":
        gz_ros2_image_bridge = Node(
            package="ros_gz_image",
            executable="image_bridge",
            namespace=gz_namespace,
            arguments=[
                f"/{namespace}/frontal_cam/image_raw",
                f"/{namespace}/ventral_cam/image_raw",
            ],
            output="screen",
        )

        nodes_to_start.append(gz_ros2_image_bridge)

    return nodes_to_start


def generate_launch_description():
    declared_arguments = [
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument("x", default_value="0"),
        DeclareLaunchArgument("y", default_value="0"),
        DeclareLaunchArgument("z", default_value="0"),
        DeclareLaunchArgument("R", default_value="0"),
        DeclareLaunchArgument("P", default_value="0"),
        DeclareLaunchArgument("Y", default_value="0"),
        DeclareLaunchArgument("sensor", default_value="camera"),
        DeclareLaunchArgument("namespace", default_value="drone"),
        DeclareLaunchArgument("entity", default_value="drone"),
    ]

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
