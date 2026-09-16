import os
import xacro
import yaml

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, OpaqueFunction, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch_ros.actions import Node


def load_yaml(package_name, file_path):
    pkg_path = get_package_share_directory(package_name)
    with open(os.path.join(pkg_path, file_path), "r") as f:
        return yaml.safe_load(f)


def load_file(package_name, file_path):
    pkg_path = get_package_share_directory(package_name)
    with open(os.path.join(pkg_path, file_path), "r") as f:
        return f.read()


def launch_setup(context):
    x = LaunchConfiguration("x")
    y = LaunchConfiguration("y")
    z = LaunchConfiguration("z")
    R = LaunchConfiguration("R")
    P = LaunchConfiguration("P")
    Y = LaunchConfiguration("Y")
    gz_namespace = LaunchConfiguration("namespace")
    gz_entity = LaunchConfiguration("entity")

    package_dir = get_package_share_directory("custom_robots")

    namespace = gz_namespace.perform(context)
    entity = gz_entity.perform(context)

    # =========================
    # ROBOT DESCRIPTION (URDF)
    # =========================
    xacro_file = os.path.join(
        package_dir,
        "models",
        "xlerobot",
        "xlerobot.urdf.xacro",
    )

    controllers_file = os.path.join(
        get_package_share_directory("xlerobot_moveit_config"),
        "config",
        "controller_manager.yaml",
    )

    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "namespace": namespace,
            "simulation_controllers": controllers_file,
        },
    ).toxml()

    robot_description = {"robot_description": robot_description_content}

    # =========================
    # MOVEIT CONFIG
    # =========================
    robot_description_semantic = {
        "robot_description_semantic": load_file(
            "xlerobot_moveit_config", "srdf/xlerobot.srdf"
        )
    }

    kinematics_yaml = load_yaml("xlerobot_moveit_config", "config/kinematics.yaml")
    kinematics_yaml = {
        "robot_description_kinematics": kinematics_yaml["/**"]["ros__parameters"]
    }

    moveit_controllers = load_yaml(
        "xlerobot_moveit_config", "config/moveit_controllers.yaml"
    )
    moveit_controllers = moveit_controllers["/**"]["ros__parameters"]

    ompl_planning = load_yaml("xlerobot_moveit_config", "config/ompl_planning.yaml")
    ompl_planning = ompl_planning["/**"]["ros__parameters"]

    planning_pipelines_config = {
        "planning_pipelines": ["ompl"],
        "default_planning_pipeline": "ompl",
        "ompl": {
            "planning_plugin": "ompl_interface/OMPLPlanner",
        },
    }

    joint_limits_yaml = load_yaml("xlerobot_moveit_config", "config/joint_limits.yaml")
    combined_planning = {"robot_description_planning": joint_limits_yaml}

    moveit_controller_manager_param = {
        "moveit_controller_manager": "moveit_simple_controller_manager/MoveItSimpleControllerManager"
    }

    # =========================
    # CORE NODES
    # =========================
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        namespace=gz_namespace,
        output="screen",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    # No static transform from world to base_footprint here on purpose, the
    # base moves through VelocityControl so nailing it to a fixed world pose
    # would be wrong the moment it drives away, arm planning stays relative
    # to the robot itself instead

    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        namespace=gz_namespace,
        arguments=[
            "-topic",
            f"/{namespace}/robot_description",
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
            f"/{namespace}/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry",
            f"/{namespace}/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",
            f"/{namespace}/head_camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",
            f"/{namespace}/left_arm_camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",
            f"/{namespace}/right_arm_camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",
        ],
        output="screen",
    )

    # the camera sensors were wired in the xacro but never actually reached
    # ROS before, sensor_msgs/Image needs ros_gz_image specifically, a plain
    # parameter_bridge line does not work for it
    gz_ros2_image_bridge = Node(
        package="ros_gz_image",
        executable="image_bridge",
        namespace=gz_namespace,
        arguments=[
            f"/{namespace}/head_camera/image",
            f"/{namespace}/left_arm_camera/image_raw",
            f"/{namespace}/right_arm_camera/image_raw",
        ],
        output="screen",
    )

    # =========================
    # CONTROLLER SPAWNERS
    # =========================
    def controller_spawner(controller_name):
        return Node(
            package="controller_manager",
            executable="spawner",
            namespace=gz_namespace,
            arguments=[controller_name],
            output="screen",
        )

    joint_state_broadcaster_spawner = controller_spawner("joint_state_broadcaster")
    left_arm_controller_spawner = controller_spawner("left_arm_controller")
    right_arm_controller_spawner = controller_spawner("right_arm_controller")
    left_gripper_controller_spawner = controller_spawner("left_gripper_controller")
    right_gripper_controller_spawner = controller_spawner("right_gripper_controller")
    head_controller_spawner = controller_spawner("head_controller")

    # =========================
    # MOVEIT NODES
    # =========================
    move_group = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        namespace=gz_namespace,
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            planning_pipelines_config,
            moveit_controllers,
            combined_planning,
            moveit_controller_manager_param,
            {"use_sim_time": True},
        ],
    )

    # The "move" executable (MoveJ/MoveL/MoveG action API) additionally loads
    # ros2srrc_robots/<ROB_PARAM>/config/joint_specifications.yaml and
    # ros2srrc_endeffectors/<EE_PARAM>/config/joint_specifications.yaml at
    # startup, and crashes immediately (uncaught YAML::BadFile) if those do
    # not exist. There is no "xlerobot"/"left_gripper"/"right_gripper" entry
    # in either package yet, and adding one means a new install(DIRECTORY ...)
    # line plus a rebuild of ros2srrc_robots/ros2srrc_endeffectors, so it is
    # left out for now, robmove/robpose/move_group below do not need it.

    left_robmove = Node(
        package="ros2srrc_execution",
        executable="robmove",
        name="left_robmove",
        namespace=gz_namespace,
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            moveit_controllers,
            ompl_planning,
            moveit_controller_manager_param,
            {"use_sim_time": True},
            {"ROB_PARAM": "xlerobot"},
            {"ROB_GROUP": "xlerobot_left_arm"},
        ],
    )

    right_robmove = Node(
        package="ros2srrc_execution",
        executable="robmove",
        name="right_robmove",
        namespace=gz_namespace,
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            moveit_controllers,
            ompl_planning,
            moveit_controller_manager_param,
            {"use_sim_time": True},
            {"ROB_PARAM": "xlerobot"},
            {"ROB_GROUP": "xlerobot_right_arm"},
        ],
    )

    left_robpose = Node(
        package="ros2srrc_execution",
        executable="robpose",
        name="left_robpose",
        namespace=gz_namespace,
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            ompl_planning,
            {"use_sim_time": True},
            {"ROB_PARAM": "xlerobot"},
            {"ROB_GROUP": "xlerobot_left_arm"},
        ],
    )

    right_robpose = Node(
        package="ros2srrc_execution",
        executable="robpose",
        name="right_robpose",
        namespace=gz_namespace,
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            ompl_planning,
            {"use_sim_time": True},
            {"ROB_PARAM": "xlerobot"},
            {"ROB_GROUP": "xlerobot_right_arm"},
        ],
    )

    moveit_nodes = [
        move_group,
        left_robmove,
        right_robmove,
        left_robpose,
        right_robpose,
    ]

    # =========================
    # STARTUP ORDER
    # =========================
    # gz_ros2_control (and its controller_manager) only exists once the entity
    # is actually spawned in Gazebo, and move_group only makes sense once the
    # controllers it talks to are active, chaining on process exit (every one
    # of these is a one shot call that exits once it is done, not a persistent
    # node) keeps that order instead of firing everything at once and hoping
    # the timing works out, which is what makes the existing UR arm launch
    # files fragile on a RAM reset
    after_spawn = RegisterEventHandler(
        OnProcessExit(
            target_action=gz_spawn_entity,
            on_exit=[joint_state_broadcaster_spawner],
        )
    )

    after_joint_state_broadcaster = RegisterEventHandler(
        OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[left_arm_controller_spawner],
        )
    )

    after_left_arm = RegisterEventHandler(
        OnProcessExit(
            target_action=left_arm_controller_spawner,
            on_exit=[right_arm_controller_spawner],
        )
    )

    after_right_arm = RegisterEventHandler(
        OnProcessExit(
            target_action=right_arm_controller_spawner,
            on_exit=[left_gripper_controller_spawner],
        )
    )

    after_left_gripper = RegisterEventHandler(
        OnProcessExit(
            target_action=left_gripper_controller_spawner,
            on_exit=[right_gripper_controller_spawner],
        )
    )

    after_right_gripper = RegisterEventHandler(
        OnProcessExit(
            target_action=right_gripper_controller_spawner,
            on_exit=[head_controller_spawner],
        )
    )

    after_head = RegisterEventHandler(
        OnProcessExit(
            target_action=head_controller_spawner,
            on_exit=moveit_nodes,
        )
    )

    return [
        robot_state_publisher_node,
        gz_spawn_entity,
        gz_ros2_bridge,
        gz_ros2_image_bridge,
        after_spawn,
        after_joint_state_broadcaster,
        after_left_arm,
        after_right_arm,
        after_left_gripper,
        after_right_gripper,
        after_head,
    ]


def generate_launch_description():
    declared_arguments = [
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument("x", default_value="0"),
        DeclareLaunchArgument("y", default_value="0"),
        DeclareLaunchArgument("z", default_value="0"),
        DeclareLaunchArgument("R", default_value="0"),
        DeclareLaunchArgument("P", default_value="0"),
        DeclareLaunchArgument("Y", default_value="0"),
        DeclareLaunchArgument("namespace", default_value="logistic_robot"),
        DeclareLaunchArgument("entity", default_value="xlerobot"),
    ]

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
