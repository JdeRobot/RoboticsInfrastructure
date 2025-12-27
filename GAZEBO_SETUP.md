# Gazebo Sim 8 (Harmonic) Setup for UR5 with Robotiq Gripper

This package has been configured for Gazebo Sim 8 (Harmonic) with ROS 2 Humble.

## Prerequisites

Install required packages:

```bash
sudo apt update
sudo apt install -y \
    ros-humble-ros-gz-sim \
    ros-humble-ros-gz-bridge \
    ros-humble-gz-ros2-control \
    ros-humble-joint-state-broadcaster \
    ros-humble-joint-trajectory-controller \
    ros-humble-position-controllers \
    ros-humble-xacro
```

## Setup Steps

### 1. Build the workspace

```bash
cd /home/anish/ur5_sim8/ROS2_pick_and_place_UR5
colcon build --symlink-install
source install/setup.bash
```

### 2. Set up Gazebo resource paths

```bash
source /home/anish/ur5_sim8/ROS2_pick_and_place_UR5/setup_gz_paths.sh
```

Or add to your `~/.bashrc`:

```bash
export GZ_SIM_RESOURCE_PATH="/home/anish/ur5_sim8/ROS2_pick_and_place_UR5:${GZ_SIM_RESOURCE_PATH}"
```

### 3. Launch Options

#### Option A: Use the launch file (Recommended)

```bash
ros2 launch ur5_gripper_description gazebo.launch.py
```

With specific UR type:

```bash
ros2 launch ur5_gripper_description gazebo.launch.py ur_type:=ur5
```

Without RViz:

```bash
ros2 launch ur5_gripper_description gazebo.launch.py launch_rviz:=false
```

#### Option B: Test URDF generation first

```bash
cd /home/anish/ur5_sim8/ROS2_pick_and_place_UR5
python3 test_urdf_generation.py
```

This will generate the URDF at `/tmp/ur5_robotiq_gripper.urdf` which you can then inspect or load into Gazebo.

#### Option C: Manual process

```bash
# Process xacro to URDF
xacro ur5_gripper_description/urdf/ur5_robotiq85_gripper.urdf.xacro \
    ur_type:=ur5 \
    sim_ignition:=true \
    simulation_controllers:=$(pwd)/ur5_gripper_description/config/ur5_controllers.yaml \
    > /tmp/ur5_robot.urdf

# Launch Gazebo Sim
gz sim -r empty.sdf &

# Spawn the robot
ros2 run ros_gz_sim create -topic robot_description -file /tmp/ur5_robot.urdf
```

## Testing the Robot

### Check available topics

```bash
ros2 topic list
```

You should see topics like:
- `/joint_states`
- `/joint_trajectory_controller/joint_trajectory`
- `/gripper_controller/gripper_cmd`

### Control the robot arm

```bash
# Send a joint trajectory command
ros2 topic pub /joint_trajectory_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{
  joint_names: ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint', 'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint'],
  points: [
    {positions: [0.0, -1.57, 0.0, -1.57, 0.0, 0.0], time_from_start: {sec: 2}}
  ]
}"
```

### Control the gripper

```bash
# Open gripper
ros2 action send_goal /gripper_controller/gripper_cmd control_msgs/action/GripperCommand "{command: {position: 0.0, max_effort: 50.0}}"

# Close gripper
ros2 action send_goal /gripper_controller/gripper_cmd control_msgs/action/GripperCommand "{command: {position: 0.8, max_effort: 50.0}}"
```

## Troubleshooting

### Error: "A model must have at least one link"

- Don't load `.xacro` files directly into Gazebo
- Process with xacro first: `xacro file.xacro > file.urdf`

### Error: "cannot find package"

- Make sure you've sourced the workspace: `source install/setup.bash`
- Rebuild with: `colcon build --symlink-install`

### Meshes not found

- Set resource path: `source setup_gz_paths.sh`
- Or add to ~/.bashrc: `export GZ_SIM_RESOURCE_PATH="/home/anish/ur5_sim8/ROS2_pick_and_place_UR5:${GZ_SIM_RESOURCE_PATH}"`

## Key Changes for Gazebo Sim 8 (Harmonic)

1. Updated plugin names:
   - `libign_ros2_control-system.so` → `gz_ros2_control-system`
   - `ign_ros2_control/IgnitionSystem` → Standard Gazebo Sim plugin

2. Updated FT sensor plugin configuration for ROS 2 style topics

3. Added proper ros2_control configuration for gripper with mimic joints

4. Created controller configuration file for arm and gripper

5. Launch file uses `ros_gz_sim` instead of deprecated `gazebo_ros`
