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
    end_effector = LaunchConfiguration("end_effector").perform(context)
    harvest = end_effector == "harvest"
    # Config files of the harvest head carry a suffix
    suffix = "_harvest" if harvest else ""

    package_dir = get_package_share_directory("custom_robots")

    namespace = gz_namespace.perform(context)
    entity = gz_entity.perform(context)

    # Robot description
    xacro_file = os.path.join(
        package_dir,
        "models",
        "mmo500",
        "mmo500.urdf.xacro",
    )

    controllers_file = os.path.join(
        get_package_share_directory("mmo500_moveit_config"),
        "config",
        f"controller_manager{suffix}.yaml",
    )

    robot_description_content = xacro.process_file(
        xacro_file,
        mappings={
            "namespace": namespace,
            "simulation_controllers": controllers_file,
            "end_effector": end_effector,
        },
    ).toxml()

    robot_description = {"robot_description": robot_description_content}

    # MoveIt configuration
    robot_description_semantic = {
        "robot_description_semantic": load_file(
            "mmo500_moveit_config", f"srdf/mmo500{suffix}.srdf"
        )
    }

    kinematics_yaml = load_yaml("mmo500_moveit_config", "config/kinematics.yaml")
    kinematics_yaml = {
        "robot_description_kinematics": kinematics_yaml["/**"]["ros__parameters"]
    }

    moveit_controllers = load_yaml(
        "mmo500_moveit_config", f"config/moveit_controllers{suffix}.yaml"
    )
    moveit_controllers = moveit_controllers["/**"]["ros__parameters"]

    ompl_planning = load_yaml("mmo500_moveit_config", "config/ompl_planning.yaml")
    ompl_planning = ompl_planning["/**"]["ros__parameters"]

    # Pilz provides the LIN and PTP planners used by Robmove
    planning_pipelines_config = {
        "planning_pipelines": ["ompl", "pilz_industrial_motion_planner"],
        "default_planning_pipeline": "pilz_industrial_motion_planner",
        "ompl": {
            "planning_plugin": "ompl_interface/OMPLPlanner",
        },
        "pilz_industrial_motion_planner": {
            "planning_plugin": "pilz_industrial_motion_planner/CommandPlanner",
            "request_adapters": "",
            "start_state_max_bounds_error": 0.1,
            "default_planner_config": "PTP",
        },
    }

    joint_limits_yaml = load_yaml("mmo500_moveit_config", "config/joint_limits.yaml")
    pilz_cartesian_limits = load_yaml(
        "mmo500_moveit_config", "config/pilz_cartesian_limits.yaml"
    )
    combined_planning = {
        "robot_description_planning": {**joint_limits_yaml, **pilz_cartesian_limits}
    }

    moveit_controller_manager_param = {
        "moveit_controller_manager": "moveit_simple_controller_manager/MoveItSimpleControllerManager"
    }

    # Core nodes
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        namespace=gz_namespace,
        output="screen",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    # No world transform because planning stays relative to base_footprint
    map_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=[x, y, z, R, P, Y, "map", "odom"],
    )

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

    bridge_arguments = [
        f"/{namespace}/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry",
        f"/{namespace}/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",
        f"/{namespace}/front_laser/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
        f"/{namespace}/back_laser/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
        f"/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V",
    ]
    if harvest:
        bridge_arguments.append(
            f"/{namespace}/harvest_camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo"
        )

    gz_ros2_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        namespace=gz_namespace,
        arguments=bridge_arguments,
        output="screen",
    )

    # Images use ros_gz_image because the parameter bridge does not support them
    camera_image_bridge = Node(
        package="ros_gz_image",
        executable="image_bridge",
        namespace=gz_namespace,
        arguments=[
            f"/{namespace}/harvest_camera/image",
            f"/{namespace}/harvest_camera/depth_image",
        ],
        output="screen",
    )

    # Controller spawners
    def controller_spawner(controller_name):
        return Node(
            package="controller_manager",
            executable="spawner",
            namespace=gz_namespace,
            # Long timeouts because the scene is still loading
            arguments=[
                controller_name,
                "--switch-timeout",
                "90",
                "--controller-manager-timeout",
                "90",
                "--service-call-timeout",
                "90",
            ],
            output="screen",
        )

    joint_state_broadcaster_spawner = controller_spawner("joint_state_broadcaster")
    arm_controller_spawner = controller_spawner("arm_controller")
    gripper_controller_spawner = controller_spawner("gripper_controller")
    twist_controller_spawner = controller_spawner("twist_controller")

    # MoveIt nodes
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

    # No move executable because mmo500 has no joint_specifications.yaml
    robmove = Node(
        package="ros2srrc_execution",
        executable="robmove",
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
            {"ROB_PARAM": "mmo500"},
            {"ROB_GROUP": "ur10_manipulator"},
            {"ACTION_NAME": f"/{namespace}/Robmove"},
        ],
    )

    robpose = Node(
        package="ros2srrc_execution",
        executable="robpose",
        name="robpose",
        namespace=gz_namespace,
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
            ompl_planning,
            {"use_sim_time": True},
            {"ROB_PARAM": "mmo500"},
            {"ROB_GROUP": "ur10_manipulator"},
        ],
    )

    moveit_nodes = [move_group, robmove, robpose]

    # Startup order
    # Each step starts when the previous one exits
    after_spawn = RegisterEventHandler(
        OnProcessExit(
            target_action=gz_spawn_entity,
            on_exit=[joint_state_broadcaster_spawner],
        )
    )

    after_joint_state_broadcaster = RegisterEventHandler(
        OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[arm_controller_spawner],
        )
    )

    after_arm = RegisterEventHandler(
        OnProcessExit(
            target_action=arm_controller_spawner,
            on_exit=[gripper_controller_spawner],
        )
    )

    # The harvest head also twists, its controller goes before MoveIt
    last_spawner = gripper_controller_spawner
    after_twist = []
    if harvest:
        after_twist = [
            RegisterEventHandler(
                OnProcessExit(
                    target_action=gripper_controller_spawner,
                    on_exit=[twist_controller_spawner],
                )
            )
        ]
        last_spawner = twist_controller_spawner

    after_gripper = RegisterEventHandler(
        OnProcessExit(
            target_action=last_spawner,
            on_exit=moveit_nodes,
        )
    )

    bridges = [gz_ros2_bridge, camera_image_bridge] if harvest else [gz_ros2_bridge]

    return [
        robot_state_publisher_node,
        gz_spawn_entity,
        *bridges,
        after_spawn,
        after_joint_state_broadcaster,
        after_arm,
        *after_twist,
        after_gripper,
        map_tf,
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
        DeclareLaunchArgument("namespace", default_value="mmo500"),
        DeclareLaunchArgument("entity", default_value="mmo500"),
        # robotiq or harvest
        DeclareLaunchArgument("end_effector", default_value="robotiq"),
    ]

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
