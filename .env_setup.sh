#!/bin/bash
# Environment setup script for UR5 Gazebo Harmonic workspace
# Source this file or add these lines to your ~/.bashrc

# Gazebo Harmonic version
export GZ_VERSION=harmonic

# ROS 2 Humble
source /opt/ros/humble/setup.bash

# This workspace (update path if different)
WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${WORKSPACE_DIR}/install/setup.bash"

# Gazebo plugin paths for gz_ros2_control
export GZ_SIM_SYSTEM_PLUGIN_PATH=${GZ_SIM_SYSTEM_PLUGIN_PATH}:${WORKSPACE_DIR}/install/gz_ros2_control/lib

# Gazebo resource path (for finding meshes and models)
export GZ_SIM_RESOURCE_PATH=${WORKSPACE_DIR}:${GZ_SIM_RESOURCE_PATH}

echo "✓ Environment configured for UR5 Gazebo Harmonic workspace"
echo "  Workspace: ${WORKSPACE_DIR}"
echo "  GZ_VERSION: ${GZ_VERSION}"
