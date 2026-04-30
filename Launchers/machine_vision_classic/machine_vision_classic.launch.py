#!/usr/bin/python3

# ===================================== COPYRIGHT ===================================== #
#                                                                                       #
#  IFRA (Intelligent Flexible Robotics and Assembly) Group, CRANFIELD UNIVERSITY        #
#  Created on behalf of the IFRA Group at Cranfield University, United Kingdom          #
#  E-mail: IFRA@cranfield.ac.uk                                                         #
#                                                                                       #
#  Licensed under the Apache-2.0 License.                                               #
#  You may not use this file except in compliance with the License.                     #
#  You may obtain a copy of the License at: http://www.apache.org/licenses/LICENSE-2.0  #
#                                                                                       #
#  Unless required by applicable law or agreed to in writing, software distributed      #
#  under the License is distributed on an "as-is" basis, without warranties or          #
#  conditions of any kind, either express or implied. See the License for the specific  #
#  language governing permissions and limitations under the License.                    #
#                                                                                       #
#  IFRA Group - Cranfield University                                                    #
#  AUTHORS: Mikel Bueno Viso - Mikel.Bueno-Viso@cranfield.ac.uk                         #
#           Dr. Seemal Asif  - s.asif@cranfield.ac.uk                                   #
#           Prof. Phil Webb  - p.f.webb@cranfield.ac.uk                                 #
#                                                                                       #
#  Date: June, 2024.                                                                    #
#                                                                                       #
# ===================================== COPYRIGHT ===================================== #

# ======= CITE OUR WORK ======= #
# You can cite our work with the following statement:
# IFRA-Cranfield (2023) ROS 2 Sim-to-Real Robot Control. URL: https://github.com/IFRA-Cranfield/ros2_SimRealRobotControl.

# moveit2.launch.py:
# Launch file for the Robot's GAZEBO SIMULATION + MoveIt!2 Framework in ROS2 Humble:

# Import libraries:
import os, sys, xacro, yaml
from ament_index_python.packages import get_package_share_directory, PackageNotFoundError
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, RegisterEventHandler, TimerAction
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from moveit_configs_utils import MoveItConfigsBuilder
from launch.actions import SetEnvironmentVariable

# LOAD FILE:
def load_file(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)
    try:
        with open(absolute_file_path, 'r') as file:
            return file.read()
    except EnvironmentError:
        # parent of IOError, OSError *and* WindowsError where available.
        return None
        
# LOAD YAML:
def load_yaml(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)
    try:
        with open(absolute_file_path, 'r') as file:
            return yaml.safe_load(file)
    except EnvironmentError:
        # parent of IOError, OSError *and* WindowsError where available.
        return None

# ===== REQUIRED TO GET THE ROBOT CONFIGURATION === #

# EVALUATE INPUT ARGUMENTS:
def AssignArgument(ARGUMENT):
    ARGUMENTS = sys.argv
    for y in ARGUMENTS:
        if (ARGUMENT + ":=") in y:
            ARG = y.replace((ARGUMENT + ":="),"")
            return(ARG)

# GET CONFIGURATION from YAML:
def GetCONFIG(CONFIGURATION, PKG_PATH):
    
    RESULT = {"Success": False, "ID": "", "Name": "", "urdf": "", "ee": ""}
    
    YAML_PATH = PKG_PATH + "/config/configurations.yaml"
    
    if not os.path.exists(YAML_PATH):
        return (RESULT)
    
    with open(YAML_PATH, 'r') as YAML:
        cYAML = yaml.safe_load(YAML)

    for x in cYAML["Configurations"]:

        if x["ID"] == CONFIGURATION:
            RESULT["Success"] = True
            RESULT["ID"] = x["ID"]
            RESULT["Name"] = x["Name"]
            RESULT["urdf"] = x["urdf"]
            RESULT["rob"] = x["rob"]
            RESULT["ee"] = x["ee"]

    return(RESULT)

# GET EE-Controllers LIST:
def GetEEctr(EEName):
    
    RESULT = []

    PATH = os.path.join(get_package_share_directory('ros2srrc_endeffectors'), EEName, 'config')
    YAML_PATH = PATH + "/controller_moveit2.yaml"
    
    with open(YAML_PATH, 'r') as YAML:
        cYAML = yaml.safe_load(YAML)

    for x in cYAML["controller_names"]:
        RESULT.append(x)

    return(RESULT)

# CHECK if CONTROLLER file exists for EE:

def EEctrlEXISTS(EEName):
    
    PATH = os.path.join(get_package_share_directory('ros2srrc_endeffectors'), EEName, 'config')
    YAML_PATH = PATH + "/controller.yaml"
    
    RES = os.path.exists(YAML_PATH)
    return(RES)
def setup_gazebo_environment():
    """Setup Gazebo environment variables for both local and Docker"""
    
    # Always disable online model database (fixes hanging issue)
    env_vars = [
        SetEnvironmentVariable(name='GAZEBO_MODEL_DATABASE_URI', value='')
    ]
    
    # Detect environment and set appropriate model path
    if os.path.exists('/dev_ws'):
        # Docker environment
        model_path = '/dev_ws/src/IndustrialRobots/ros2_SimRealRobotControl/packages/ur5/ros2srrc_ur5_gazebo/models'
    else:
        # Local environment
        model_path = '/home/shu/dev_ws/src/IndustrialRobots/ros2_SimRealRobotControl/packages/ur5/ros2srrc_ur5_gazebo/models'
    
    # Get existing GAZEBO_MODEL_PATH and append our path
    existing_path = os.environ.get('GAZEBO_MODEL_PATH', '')
    if existing_path:
        full_path = f"{model_path}:{existing_path}"
    else:
        full_path = model_path
    
    env_vars.append(
        SetEnvironmentVariable(name='GAZEBO_MODEL_PATH', value=full_path)
    )
    
    return env_vars
# ========== **GENERATE LAUNCH DESCRIPTION** ========== #
def generate_launch_description():

    LD = LaunchDescription()

    gazebo_env_vars = setup_gazebo_environment()
    for env_var in gazebo_env_vars:
        LD.add_action(env_var)
    
    # === INPUT ARGUMENT: ROS 2 PACKAGE === #
    
    #PACKAGE_NAME = AssignArgument("package")
    # DMM: fixed UR5
    PACKAGE_NAME = "ros2srrc_ur5"
    
    if PACKAGE_NAME != None:
        None
    else:
        print("")
        print("ERROR: package INPUT ARGUMENT has not been defined. Please try again.")
        print("Closing... BYE!")
        exit()
        
    # CHECK if -> PACKAGE EXISTS, and GET PATH:
    try:
        PKG_PATH = get_package_share_directory(PACKAGE_NAME + "_gazebo")
    except PackageNotFoundError:
        print("")
        print("ERROR: The defined ROS 2 Package was not found. Please try again.")
        print("Closing... BYE!")
        exit()
    except ValueError:
        print("")
        print("ERROR: The defined ROS 2 Package name is not valid. Please try again.")
        print("Closing... BYE!")
        exit()
    
    # === INPUT ARGUMENT: CONFIGURATION === #
    # CONFIG = AssignArgument("config")
    # DMM fixed UR5 + Robotiq 85
    CONFIG = "ur5_7"
    CONFIGURATION = GetCONFIG(CONFIG, PKG_PATH)

    if CONFIGURATION["Success"] == False:
        print("")
        print("ERROR: config INPUT ARGUMENT has not been correctly defined. Please try again.")
        print("Closing... BYE!")
        exit()   

    # === INPUT ARGUMENT: HMI === #
    HMI = AssignArgument("hmi")
    if HMI == "True" or HMI == "true":
        HMI = "true"
    else:
        HMI = "false"

    # ========== CELL INFORMATION ========== #
    print("")
    print("===== GAZEBO: Robot Simulation + MoveIt!2 Framework (" + PACKAGE_NAME + "_moveit2) =====")
    print("Robot configuration:")
    print(CONFIGURATION["ID"] + " -> " + CONFIGURATION["Name"])
    print("")
    
    # ***** GAZEBO ***** #   
    # DECLARE Gazebo WORLD file:
    robot_gazebo = os.path.join(
        get_package_share_directory(PACKAGE_NAME + '_gazebo'),
        'worlds',
        PACKAGE_NAME +'_machine_vision'+ '.world')
    # DECLARE Gazebo LAUNCH file:
    gazebo = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(get_package_share_directory('gazebo_ros'), 'launch'), '/gazebo.launch.py']),
                launch_arguments={'world': robot_gazebo}.items(),
            )

    # ***** ROBOT DESCRIPTION ***** #
    # Robot Description file package:
    robot_description_path = os.path.join(get_package_share_directory(PACKAGE_NAME + '_gazebo'))
    # ROBOT urdf file path:
    xacro_file = os.path.join(robot_description_path,'urdf',CONFIGURATION["urdf"])
    # Generate ROBOT_DESCRIPTION variable:
    doc = xacro.parse(open(xacro_file))
    
    if CONFIGURATION["ee"] == "none":
        EE = "false"
    else: 
        EE = "true"
    
    xacro.process_doc(doc, mappings={
        "EE": EE,
        "EE_name": CONFIGURATION["ee"],
        "hmi": HMI,
    })
    
    # EE -> Controller file needed?
    if EE == "true":
        if EEctrlEXISTS(CONFIGURATION["ee"]) == False:
            EE = "true-NOctr"
    
    robot_description_config = doc.toxml()
    robot_description = {'robot_description': robot_description_config}

    # ROBOT STATE PUBLISHER NODE:
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='both',
        parameters=[
            robot_description,
            {"use_sim_time": True}
        ]
    )
    static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_transform_publisher",
        output="log",
        arguments=["0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "world", "base_link"],
    )

    # SPAWN ROBOT TO GAZEBO:
    spawn_entity = Node(package='gazebo_ros', executable='spawn_entity.py',
                        arguments=['-topic', 'robot_description', '-entity', CONFIGURATION["rob"]],
                        output='both')

    # ***** CONTROLLERS ***** #
    # Joint STATE BROADCASTER:
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
    )
    # Joint TRAJECTORY Controller:
    joint_trajectory_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_trajectory_controller", "-c", "/controller_manager"],
    )

    # EE CONTROLLERS:
    if EE == "true":
        CONTROLLERS = GetEEctr(CONFIGURATION["ee"])
        CONTROLLER_NODES = []

        for x in CONTROLLERS:
            CONTROLLER_NODES.append(
                Node(
                    package="controller_manager",
                    executable="spawner",
                    arguments=[x, "-c", "/controller_manager"],
                )
            )

    # *********************** MoveIt!2 *********************** #   

    # Determine SRDF file path
    if (EE == "false"):
        srdf_file_path = "config/" + CONFIGURATION["rob"] + ".srdf"
    else:
        srdf_file_path = "config/" + CONFIGURATION["rob"] + CONFIGURATION["ee"] + ".srdf"

    # Build MoveIt configuration using MoveItConfigsBuilder
    moveit_config_builder = MoveItConfigsBuilder(PACKAGE_NAME + "_moveit2")
    
    # Configure robot description semantic (SRDF)
    moveit_config_builder = moveit_config_builder.robot_description_semantic(
        file_path=srdf_file_path
    )
    
    # Configure kinematics
    moveit_config_builder = moveit_config_builder.robot_description_kinematics(
        file_path=os.path.join(
            get_package_share_directory("ros2srrc_robots"),
            CONFIGURATION["rob"], "config", "kinematics.yaml"
        )
    )
    
    # Configure joint limits
    if (EE == "false") or (EE == "true-NOctr"):
        joint_limits_yaml = load_yaml("ros2srrc_robots", CONFIGURATION["rob"] + "/config/joint_limits.yaml")
        joint_limits_file = os.path.join(
            get_package_share_directory("ros2srrc_robots"),
            CONFIGURATION["rob"], "config", "joint_limits.yaml"
        )
    else:
        # Properly merge robot and end-effector joint limits
        YAML_ROB = load_yaml("ros2srrc_robots", CONFIGURATION["rob"] + "/config/joint_limits.yaml")["joint_limits"]
        YAML_EE = load_yaml("ros2srrc_endeffectors", CONFIGURATION["ee"] + "/config/joint_limits.yaml")["joint_limits"]
        joint_limits_yaml = {}
        joint_limits_yaml["joint_limits"] = YAML_ROB | YAML_EE
        # For MoveItConfigsBuilder, we still use robot file (builder will be overridden by merged limits)
        joint_limits_file = os.path.join(
            get_package_share_directory("ros2srrc_robots"),
            CONFIGURATION["rob"], "config", "joint_limits.yaml"
        )

    joint_limits = {'robot_description_planning': joint_limits_yaml}
    
    # Configure MoveItConfigsBuilder with robot joint limits file
    moveit_config_builder = moveit_config_builder.joint_limits(
        file_path=joint_limits_file
    )
    
    # Configure planning scene monitor
    moveit_config_builder = moveit_config_builder.planning_scene_monitor(
        publish_robot_description=True, 
        publish_robot_description_semantic=True,
        publish_geometry_updates=True,
        publish_state_updates=True,
        publish_transforms_updates=True
    )
    
    # Configure trajectory execution - using robot controller config file
    controller_config_path = os.path.join(
        get_package_share_directory("ros2srrc_robots"),
        CONFIGURATION["rob"], "config", "controller_moveit2.yaml"
    )
    moveit_config_builder = moveit_config_builder.trajectory_execution(
        file_path=controller_config_path
    )
    
    # Configure planning pipelines
    moveit_config_builder = moveit_config_builder.planning_pipelines(
        pipelines=["pilz_industrial_motion_planner"]
    )
    
    # Configure Pilz cartesian limits
    moveit_config_builder = moveit_config_builder.pilz_cartesian_limits(
        file_path=os.path.join(
            get_package_share_directory("ros2srrc_robots"),
            CONFIGURATION["rob"], "config", "pilz_cartesian_limits.yaml"
        )
    )
    
    # Add sensor configuration if available
    sensors_3d_file = os.path.join(
        get_package_share_directory(PACKAGE_NAME + "_moveit2"),
        "config", "sensors_3d.yaml"
    )
    if os.path.exists(sensors_3d_file):
        moveit_config_builder = moveit_config_builder.sensors_3d(
            file_path=sensors_3d_file
        )
    
    # Build the configuration
    moveit_config = moveit_config_builder.to_moveit_configs()

    # Load additional configurations that need merging for EE
    kinematics_yaml = load_yaml("ros2srrc_robots", CONFIGURATION["rob"] + "/config/kinematics.yaml")
    pilz_cartesian_limits_yaml = load_yaml("ros2srrc_robots", CONFIGURATION["rob"] + "/config/pilz_cartesian_limits.yaml")
    
    # Add Pilz planner configuration
    pilz_planning_pipeline_config = {
        "move_group": {
            "planning_plugin": "pilz_industrial_motion_planner/CommandPlanner",
            "request_adapters": "",
            "start_state_max_bounds_error": 0.1,
            "default_planner_config": "PTP",
        }
    }

    # Add controller configuration for MoveIt
    if (EE == "false") or (EE == "true-NOctr"):
        moveit_simple_controllers_yaml = load_yaml("ros2srrc_robots", CONFIGURATION["rob"] + "/config/controller_moveit2.yaml")
    else:
        # Properly merge robot and end-effector controller configs
        YAML_ROB = load_yaml("ros2srrc_robots", CONFIGURATION["rob"] + "/config/controller_moveit2.yaml")
        YAML_EE = load_yaml("ros2srrc_endeffectors", CONFIGURATION["ee"] + "/config/controller_moveit2.yaml")
        for x in YAML_ROB["controller_names"]:
            YAML_EE["controller_names"].append(x)
        moveit_simple_controllers_yaml = YAML_ROB | YAML_EE

    # Use the same structure as the backup file
    moveit_controllers = {
        "moveit_simple_controller_manager": moveit_simple_controllers_yaml,
        "moveit_controller_manager": "moveit_simple_controller_manager/MoveItSimpleControllerManager",
    }

    # Add trajectory execution parameters from backup
    trajectory_execution = {
        "moveit_manage_controllers": True,
        "trajectory_execution.allowed_execution_duration_scaling": 1.2,
        "trajectory_execution.allowed_goal_duration_margin": 0.5,
        "trajectory_execution.allowed_start_tolerance": 0.01,
    }

    # Add planning scene monitor parameters from backup
    planning_scene_monitor_parameters = {
        "publish_planning_scene": True,
        "publish_geometry_updates": True,
        "publish_state_updates": True,
        "publish_transforms_updates": True,
    }

    # CRITICAL: Add MoveGroup capabilities for gripper planning
    move_group_capabilities = {
        "capabilities": "pilz_industrial_motion_planner/MoveGroupSequenceAction pilz_industrial_motion_planner/MoveGroupSequenceService"
    }

        # MoveGroup Node - keep original planning scene structure
    run_move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            robot_description,  # Add the robot description from earlier
            moveit_config.to_dict(),
            pilz_planning_pipeline_config,
            joint_limits,  # This is critical - contains merged joint limits with acceleration limits for gripper
            moveit_controllers,
            {
                "use_sim_time": True,
                "trajectory_execution.allowed_execution_duration_scaling": 1.2,
                "trajectory_execution.allowed_goal_duration_margin": 0.5,
                "trajectory_execution.allowed_start_tolerance": 0.01,
                "moveit_manage_controllers": True,
                "planning_pipelines": ["move_group"],
                # "default_planning_pipeline": "move_group",
                "default_planning_pipeline": "move_group",

                "publish_geometry_updates": False,
                "publish_planning_scene": False,

                # Octomap parameters
                "octomap_resolution": 0.02,  # Default is 0.1, smaller = finer resolution
                "octomap_frame": "world",
                "max_range": 5.0,
            },
        ],
        arguments=["--ros-args", "--log-level", "info"],
    )

    # RVIZ with all parameters from backup:
    rviz_base = os.path.join(get_package_share_directory(PACKAGE_NAME + "_moveit2"), "config")
    rviz_full_config = os.path.join(rviz_base + "/ur5robotiq_2f85_with_cam_moveit2.rviz")
    
    rviz_node_full = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_full_config],
        parameters=[
            robot_description,
            moveit_config.to_dict(),
            joint_limits,  # Add merged joint limits here too
            {"use_sim_time": True},
        ]
    )

    # =================================================================================================== #
    # ============================= ros2srrc_execution -> CUSTOM INTERFACES ============================= #

    # Move and Sequence:
    if EE == "true":

        MoveInterface = Node(
            name="move",
            package="ros2srrc_execution",
            executable="move",
            output="screen",
            parameters=[robot_description, moveit_config.robot_description_semantic, {"robot_description_kinematics": kinematics_yaml}, {"use_sim_time": True}, {"ROB_PARAM": CONFIGURATION["rob"]}, {"EE_PARAM": CONFIGURATION["ee"]}, {"ENV_PARAM": "gazebo"}],
        )

    else:

        MoveInterface = Node(
            name="move",
            package="ros2srrc_execution",
            executable="move",
            output="screen",
            parameters=[robot_description, moveit_config.robot_description_semantic, {"robot_description_kinematics": kinematics_yaml}, {"use_sim_time": True}, {"ROB_PARAM": CONFIGURATION["rob"]}, {"EE_PARAM": "none"}, {"ENV_PARAM": "gazebo"}],
        )

    # RobMove and RobPose:
    RobMoveInterface = Node(
        name="robmove",
        package="ros2srrc_execution",
        executable="robmove",
        output="screen",
        parameters=[robot_description, moveit_config.robot_description_semantic, {"robot_description_kinematics": kinematics_yaml}, {"use_sim_time": True}, {"ROB_PARAM": CONFIGURATION["rob"]}],
    )
    RobPoseInterface = Node(
        name="robpose",
        package="ros2srrc_execution",
        executable="robpose",
        output="screen",
        parameters=[robot_description, moveit_config.robot_description_semantic, {"robot_description_kinematics": kinematics_yaml}, {"use_sim_time": True}, {"ROB_PARAM": CONFIGURATION["rob"]}],
    )
    

    pcl_filter_node = Node(
        package='pcl_filter',
        executable='pcl_filter_server',
        name='pcl_filter_server',
        output='screen',
        parameters=[{"use_sim_time": True}]  # Add this to sync with simulation time
    )

    # =============================================== #
    # ========== RETURN LAUNCH DESCRIPTION ========== #

    # Add ROS 2 Nodes to LaunchDescription() element:
    LD.add_action(gazebo)
    LD.add_action(node_robot_state_publisher)
    LD.add_action(static_tf)
    LD.add_action(spawn_entity)

    LD.add_action(RegisterEventHandler(
        OnProcessExit(
            target_action = spawn_entity,
            on_exit = [
                joint_state_broadcaster_spawner,
                ]
            )
        )
    )

    LD.add_action(RegisterEventHandler(
        OnProcessExit(
            target_action = spawn_entity,
            on_exit = [
                joint_trajectory_controller_spawner,
                ]
            )
        )
    )

    if EE == "true":

        for x in CONTROLLER_NODES:

            LD.add_action(RegisterEventHandler(
                OnProcessExit(
                    target_action = joint_trajectory_controller_spawner,
                    on_exit = [
                        x,
                        ]
                    )
                )
            )

    LD.add_action(RegisterEventHandler(
        OnProcessExit(
            target_action = spawn_entity,
            on_exit = [
                
                # MoveIt!2:
                TimerAction(
                    period=2.0,
                    actions=[
                        rviz_node_full,
                        run_move_group_node,
                    ]
                ),
                
                ]
            )
        )
    )

    LD.add_action(RegisterEventHandler(
        OnProcessExit(
            target_action = spawn_entity,
            on_exit = [
                
                # Interfaces:
                TimerAction(
                    period=5.0,
                    actions=[
                        MoveInterface,
                        RobMoveInterface,
                        RobPoseInterface,
                        pcl_filter_node, 
                    ]
                ),
                
                ]
            )
        )
    )

    # ***** RETURN  ***** #
    return(LD)