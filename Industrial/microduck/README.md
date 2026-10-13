# Microduck

Pollen Robotics microduck robot assets for RoboticsInfrastructure.

## Contents
- `mujoco/`: MJCF models from microduck_rl (robot_walk.xml, scene_walk.xml, etc.)
- `urdf/`: URDF/xacro descriptions from microduck_description
- `meshes/`: STL meshes

## Notes
- MJCF models are the reference for MuJoCo-trained policies (mjlab).
- URDF is suitable for visualization; physics may differ from MuJoCo - policies may need re-validation if transferred to Gazebo.
- See https://github.com/pollen-robotics/microduck and https://github.com/pollen-robotics/microduck_rl for details.
