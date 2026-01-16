# Pick Place Harmonic - CustomRobots Directory

This directory contains resources for the Pick and Place Harmonic exercise using Gazebo Harmonic.

## Structure

- **launch/**: Launch files for the exercise
- **models/**: Symbolic link to warehouse models from robotiq_description
- **urdf/**: Symbolic link to URDF files from ur5_gripper_description

## Main Launch File

The main launcher is located in `/RoboticsInfrastructure/Launchers/pick_place_harmonic.launch.py`

This launcher wraps the `spawn_robot_warehouse.launch.py` from the `ur5_gripper_description` package,
which is part of the `pick_place_harmonic_exercise` in IndustrialRobots.

## Package Dependencies

The exercise depends on packages from:
`/home/dev_ws/src/IndustrialRobots/pick_place_harmonic_exercise/`

These must be built with colcon before the exercise can run.
