cmake_minimum_required(VERSION 3.5)
project(microduck)
find_package(ament_cmake REQUIRED)
install(
  DIRECTORY meshes mujoco urdf demo config
  DESTINATION share/${PROJECT_NAME}
)
ament_package()
