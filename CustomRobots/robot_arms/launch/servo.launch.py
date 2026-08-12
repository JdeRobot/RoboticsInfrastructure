import os
import yaml
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import xacro
from launch.actions import TimerAction, ExecuteProcess

def load_file(package_name, file_path):
    package_path = get_package_share_directory(package_name)

    with open(os.path.join(package_path, file_path), "r") as f:
        return f.read()

def load_yaml(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)

    try:
        with open(absolute_file_path, "r") as file:
            return yaml.safe_load(file)
    except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
        return None


def generate_launch_description():
    package_dir = get_package_share_directory("custom_robots")

    xacro_file = os.path.join(
        package_dir,
        "models",
        "ur3",
        "ur3.urdf.xacro",
    )

    controllers_file = os.path.join(
        package_dir,
        "config",
        "ur3_controllers.yaml",
    )

    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "ur_type": "ur3",
            "name": "ur",
            "prefix": "",
            "use_fake_hardware": "false",
            "sim_gazebo": "false",
            "sim_gz": "true",
            "simulation_controllers": controllers_file,
            "hmi": "false",
            "EE": "true",
            "EE_name": "robotiq_2f85",
            "camera": "false",
        },
    ).toxml()

    robot_description = {
        "robot_description": robot_description_content
    }

    robot_description_semantic = {
        "robot_description_semantic": load_file(
            "ros2srrc_ur3_moveit2",
            "config/ur3robotiq_2f85.srdf",
        )
    }

    kinematics_yaml = load_yaml(
        "ur3_gripper_moveit_config",
        "config/kinematics.yaml",
    )

    kinematics_yaml = {
        "robot_description_kinematics":
            kinematics_yaml["/**"]["ros__parameters"]
    }

    # Get parameters for the Servo node
    servo_yaml = load_yaml(
        "ur3_gripper_moveit_config",
        "config/ur_servo.yaml"
    )

    servo_params = {
        "moveit_servo": servo_yaml
    }

    joint_limits_yaml = load_yaml(
        "ros2srrc_robots",
        "ur3/config/joint_limits.yaml"
    )

    pilz_cartesian_limits = load_yaml(
        "ros2srrc_robots",
        "ur3/config/pilz_cartesian_limits.yaml"
    )

    combined_planning = {
        "robot_description_planning": {
            **joint_limits_yaml,
            **pilz_cartesian_limits,
        }
    }

    # Launch a standalone Servo node.
    # As opposed to a node component, this may be necessary (for example) if Servo is running on a different PC
    servo_node = Node(
        package="moveit_servo",
        executable="servo_node_main",
        parameters=[
            servo_params,
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            combined_planning,
            {"use_sim_time": True},
        ],
        arguments=["--ros-args", "--log-level", "debug"],
        output="screen",
    )

    return LaunchDescription([
        servo_node,

        TimerAction(
            period=2.0,
            actions=[
                ExecuteProcess(
                    cmd=[
                        "ros2",
                        "service",
                        "call",
                        "/servo_node/start_servo",
                        "std_srvs/srv/Trigger",
                    ],
                    output="screen",
                )
            ],
        ),
    ])