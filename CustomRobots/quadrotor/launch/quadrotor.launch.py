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
            "/robot_description",
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

    nodes_to_start.append(
        Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            namespace=gz_namespace,
            arguments=[
                f"/model/{namespace}/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry",
            ],
            output="screen",
        )
    )

    gz_ros2_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        namespace=gz_namespace,
        parameters=[
            {
                "bridge_names": [
                    "cmd_vel_bridge",
                    "arm_bridge",
                    "tf_bridge",
                    "tfs_bridge",
                ]
            },
            {"bridges.cmd_vel_bridge.ros_topic_name": f"/gz/{namespace}/cmd_vel"},
            {"bridges.cmd_vel_bridge.gz_topic_name": f"/model/{namespace}/cmd_vel"},
            {"bridges.cmd_vel_bridge.ros_type_name": "geometry_msgs/msg/Twist"},
            {"bridges.cmd_vel_bridge.gz_type_name": "gz.msgs.Twist"},
            {"bridges.cmd_vel_bridge.direction": "ROS_TO_GZ"},
            {"bridges.arm_bridge.ros_topic_name": f"/gz/{namespace}/arm"},
            {
                "bridges.arm_bridge.gz_topic_name": f"/model/{namespace}/velocity_controller/enable"
            },
            {"bridges.arm_bridge.ros_type_name": "std_msgs/msg/Bool"},
            {"bridges.arm_bridge.gz_type_name": "gz.msgs.Boolean"},
            {"bridges.arm_bridge.direction": "ROS_TO_GZ"},
            {"bridges.tf_bridge.ros_topic_name": f"/tf"},
            {"bridges.tf_bridge.gz_topic_name": f"/{namespace}/tf"},
            {"bridges.tf_bridge.ros_type_name": "tf2_msgs/msg/TFMessage"},
            {"bridges.tf_bridge.gz_type_name": "gz.msgs.Pose_V"},
            {"bridges.tf_bridge.direction": "GZ_TO_ROS"},
            {"bridges.tfs_bridge.ros_topic_name": f"/tf"},
            {"bridges.tfs_bridge.gz_topic_name": f"/{namespace}/tf_static"},
            {"bridges.tfs_bridge.ros_type_name": "tf2_msgs/msg/TFMessage"},
            {"bridges.tfs_bridge.gz_type_name": "gz.msgs.Pose_V"},
            {"bridges.tfs_bridge.direction": "GZ_TO_ROS"},
        ],
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
                "twist_frame_id": f"/{namespace}/base_link",
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
