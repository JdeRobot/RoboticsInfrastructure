#!/bin/bash
# Launch UR5 + Robotiq Gripper in Gazebo Sim with MoveIt2

WORKSPACE_DIR="/user/ur5_sim8/ROS2_pick_and_place_UR5"

echo "=========================================="
echo "Launching UR5 + Robotiq + MoveIt2"
echo "in Gazebo Sim (Harmonic)"
echo "=========================================="
echo ""

# Source workspace
cd "$WORKSPACE_DIR"
source /opt/ros/humble/setup.bash
source install/setup.bash

echo "✓ ROS 2 and workspace sourced"
echo ""
echo "Starting Gazebo Sim with MoveIt2..."
echo "This will launch:"
echo "  - Gazebo Sim with UR5 + Robotiq Gripper"
echo "  - gz_ros2_control plugin"
echo "  - MoveIt2 move_group"
echo "  - RViz2 with MoveIt interface"
echo ""

# Launch
ros2 launch ur5_gripper_moveit_config gazebo_moveit.launch.py
