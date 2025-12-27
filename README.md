# UR5 + Robotiq 85 Gripper in Gazebo Harmonic

This repository contains packages for simulating a UR5 robot with Robotiq 85 gripper in Gazebo Sim (formerly Ignition Gazebo) version 8 (Harmonic) with ROS 2 Humble, including full MoveIt2 integration for motion planning.

## Packages

- **robotiq_description**: URDF/meshes for Robotiq 85 gripper
- **ur5_gripper_description**: Combined UR5 + gripper URDF with ros2_control integration
- **ur5_gripper_moveit_config**: MoveIt2 configuration for motion planning
- **gz_ros2_control**: Gazebo Sim ros2_control plugin (submodule)

## System Requirements

- Ubuntu 22.04
- ROS 2 Humble
- Gazebo Sim (Harmonic)

## Installation

### 1. Install ROS 2 Humble

Follow the official instructions: https://docs.ros.org/en/humble/Installation.html

### 2. Install Gazebo Harmonic

```bash
sudo wget https://packages.osrfoundation.org/gazebo.gpg -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null
sudo apt update
sudo apt install gz-harmonic
```

### 3. Install ROS 2 - Gazebo Harmonic Bridge

```bash
sudo apt install ros-humble-ros-gzharmonic
```

### 4. Clone and Build Workspace

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
git clone --recurse-submodules <this-repository-url>
cd ~/ros2_ws

# Install dependencies
rosdep install --from-paths src --ignore-src -r -y

# Build
colcon build --symlink-install

# Source workspace
source install/setup.bash
```

### 5. Set Environment Variables

Add these to your `~/.bashrc`:

```bash
# Gazebo Harmonic
export GZ_VERSION=harmonic
source /opt/ros/humble/setup.bash

# Add workspace (replace with your actual path)
source ~/ros2_ws/install/setup.bash
```

Then reload:
```bash
source ~/.bashrc
```

## Usage

### Launch Gazebo with Robot Only

```bash
ros2 launch ur5_gripper_description gazebo.launch.py
```

This starts:
- Gazebo Sim with UR5 + gripper
- ros2_control controllers
- Joint state publisher

### Launch with MoveIt2

```bash
ros2 launch ur5_gripper_moveit_config gazebo_moveit.launch.py
```

This starts:
- Everything from above, plus:
- MoveIt2 move_group node
- RViz with motion planning interface

### Control the Robot

In RViz:
1. Select planning group: `ur5_manipulator` (for arm) or `gripper` (for gripper)
2. Drag the interactive marker to desired pose
3. Click "Plan" to generate trajectory
4. Click "Execute" to run the motion

Use predefined poses from dropdown for quick testing.

## Controller Information

### Available Controllers

- `joint_state_broadcaster`: Publishes joint states
- `joint_trajectory_controller`: Controls 6 arm joints
- `gripper_controller`: Controls gripper (follow_joint_trajectory interface)

### Spawning Controllers Manually

```bash
ros2 control load_controller --set-state active joint_state_broadcaster
ros2 control load_controller --set-state active joint_trajectory_controller  
ros2 control load_controller --set-state active gripper_controller
```

### Check Controller Status

```bash
ros2 control list_controllers
```

## Troubleshooting

### Controllers not loading

Make sure gz_ros2_control environment variables are set:
```bash
export GZ_SIM_SYSTEM_PLUGIN_PATH=${GZ_SIM_SYSTEM_PLUGIN_PATH}:~/ros2_ws/install/gz_ros2_control/lib
```

### Gazebo crashes or doesn't find models

Check resource path:
```bash
export GZ_SIM_RESOURCE_PATH=~/ros2_ws/src/<repo-name>:${GZ_SIM_RESOURCE_PATH}
```

### RViz shows no robot

Verify robot_description topic:
```bash
ros2 topic echo /robot_description --once
```

### MoveIt planning fails

Check that controllers are active:
```bash
ros2 control list_controllers
```

All controllers should show `active` state.

## Configuration Files

Key configuration files you may want to modify:

- `ur5_gripper_description/config/ur5_controllers.yaml` - Controller parameters
- `ur5_gripper_moveit_config/config/kinematics.yaml` - IK solver settings
- `ur5_gripper_moveit_config/config/ompl_planning.yaml` - Motion planner configuration
- `ur5_gripper_moveit_config/srdf/ur5_robotiq.srdf` - Semantic robot description

## Project Structure

```
.
├── robotiq_description/          # Gripper URDF and meshes
│   ├── meshes/
│   └── urdf/
├── ur5_gripper_description/      # Combined robot description
│   ├── config/                   # Controller configs
│   ├── launch/                   # Gazebo launch files
│   ├── meshes/                   # UR5 meshes
│   └── urdf/                     # URDF/xacro files
├── ur5_gripper_moveit_config/    # MoveIt configuration
│   ├── config/                   # MoveIt configs
│   ├── launch/                   # MoveIt launch files
│   ├── rviz/                     # RViz configs
│   └── srdf/                     # Semantic description
└── gz_ros2_control/              # Gazebo ros2_control plugin
```

## Known Issues

- Gripper mimic joints show informational warnings (safe to ignore)
- Initial inertia warnings for gripper links (cosmetic only)

## References

<!-- Add your references here -->
- ✅ Gripper controller
- ✅ Joint state broadcaster
- ✅ Force/torque sensor plugin (commented - may need adaptation)

## Testing the Robot

### Check Topics

```bash
ros2 topic list
```

Expected topics:
- `/joint_states`
- `/joint_trajectory_controller/joint_trajectory`
- `/gripper_controller/gripper_cmd`

### Control the Arm

```bash
# Move to home position
ros2 topic pub --once /joint_trajectory_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{
  joint_names: ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint', 'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint'],
  points: [{positions: [0.0, -1.57, 0.0, -1.57, 0.0, 0.0], time_from_start: {sec: 2}}]
}"
```

### Control the Gripper

```bash
# Close gripper
ros2 action send_goal /gripper_controller/gripper_cmd control_msgs/action/GripperCommand "{command: {position: 0.8, max_effort: 50.0}}"

# Open gripper
ros2 action send_goal /gripper_controller/gripper_cmd control_msgs/action/GripperCommand "{command: {position: 0.0, max_effort: 50.0}}"
```

## Package Structure

```
ROS2_pick_and_place_UR5/
├── gz_ros2_control/          # Gazebo Sim ros2_control plugin
├── robotiq_description/       # Robotiq gripper URDF & meshes
├── ur5_gripper_description/   # Main package
│   ├── config/
│   │   ├── ur5_controllers.yaml       # Controller configuration
│   │   └── ur5/                       # UR5-specific parameters
│   ├── launch/
│   │   ├── gazebo.launch.py           # Main Gazebo launch file
│   │   └── view_ur.launch.py          # RViz visualization
│   ├── urdf/
│   │   ├── ur5_robotiq85_gripper.urdf.xacro  # Main robot description
│   │   ├── ur.urdf.xacro              # UR arm base
│   │   └── ur_macro.xacro             # UR arm macro
│   └── meshes/                        # 3D models for visualization
├── launch_gazebo.sh           # Quick launch script
└── GAZEBO_SETUP.md           # Detailed setup guide
```

## Troubleshooting

### Robot doesn't appear
- Check Gazebo resource path is set: `echo $GZ_SIM_RESOURCE_PATH`
- Verify workspace is sourced: `echo $ROS_PACKAGE_PATH`

### Controllers not loading  
- Check controller manager: `ros2 control list_controllers`
- View controller manager output for errors

## Refrences

- Gazebo Sim Documentation: https://gazebosim.org
- gz_ros2_control: https://github.com/ros-controls/gz_ros2_control
- ROS 2 Control: https://control.ros.org
- ur5 Description: https://github.com/JuoTungChen/ROS2_pick_and_place_UR5.git
- ur5-https://github.com/UniversalRobots
---

**Status**: ✅ Ready to launch and test!

