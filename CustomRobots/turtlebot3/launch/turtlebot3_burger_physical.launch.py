import os
import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch_ros.actions import Node


def launch_setup(context):
    gz_namespace = LaunchConfiguration("namespace")
    namespace = gz_namespace.perform(context)
    lds = LaunchConfiguration("lds").perform(context)
    usb_port = LaunchConfiguration("usb_port").perform(context)
    lds_port = LaunchConfiguration("lds_port").perform(context)

    package_dir = get_package_share_directory("custom_robots")

    xacro_file = os.path.join(
        package_dir,
        "models",
        "turtlebot3",
        "turtlebot3_burger.urdf.xacro",
    )

    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={"camera": "false", "noise_level": "none", "namespace": namespace},
    ).toxml()

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        namespace=gz_namespace,
        output="screen",
        parameters=[
            {"robot_description": robot_description_content},
            {"use_sim_time": False},
        ],
    )

    # OpenCR board, motors, IMU and wheel odometry on the same topics as the simulated Burger
    turtlebot3_node = Node(
        package="turtlebot3_node",
        executable="turtlebot3_ros",
        namespace=gz_namespace,
        output="screen",
        parameters=[os.path.join(package_dir, "config", "burger_physical.yaml")],
        arguments=["-i", usb_port],
    )

    # The namespace is not passed as a parameter since the drivers would prefix the frame ids with it
    if lds == "LDS-02":
        lidar_node = Node(
            package="ld08_driver",
            executable="ld08_driver",
            name="ld08_driver",
            namespace=gz_namespace,
            output="screen",
            parameters=[{"frame_id": "base_scan"}],
            remappings=[("scan", "laser/scan")],
        )
    else:
        lidar_node = Node(
            package="hls_lfcd_lds_driver",
            executable="hlds_laser_publisher",
            name="hlds_laser_publisher",
            namespace=gz_namespace,
            output="screen",
            parameters=[{"port": lds_port, "frame_id": "base_scan"}],
            remappings=[("scan", "laser/scan")],
        )

    # A real robot has no ground truth so the wheel odometry, with its real drift, is also the noisy one
    odom_relay_node = Node(
        package="topic_tools",
        executable="relay",
        name="odom_noisy_relay",
        namespace=gz_namespace,
        output="screen",
        arguments=["odom", "odom_noisy"],
    )

    return [robot_state_publisher_node, turtlebot3_node, lidar_node, odom_relay_node]


def generate_launch_description():
    declared_arguments = [
        DeclareLaunchArgument("use_sim_time", default_value="false"),
        # Pose arguments are unused, RAM passes them to every robot launch
        DeclareLaunchArgument("x", default_value="0"),
        DeclareLaunchArgument("y", default_value="0"),
        DeclareLaunchArgument("z", default_value="0"),
        DeclareLaunchArgument("R", default_value="0"),
        DeclareLaunchArgument("P", default_value="0"),
        DeclareLaunchArgument("Y", default_value="0"),
        DeclareLaunchArgument("entity", default_value="turtlebot3"),
        DeclareLaunchArgument("namespace", default_value="turtlebot3"),
        # LDS-01 is the older lidar and LDS-02 ships with the 2022+ Burgers
        DeclareLaunchArgument(
            "lds", default_value=os.environ.get("LDS_MODEL", "LDS-01")
        ),
        DeclareLaunchArgument("usb_port", default_value="/dev/ttyACM0"),
        # The LDS-02 driver finds its port by itself
        DeclareLaunchArgument("lds_port", default_value="/dev/ttyUSB0"),
    ]

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
