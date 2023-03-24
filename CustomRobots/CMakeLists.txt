cmake_minimum_required(VERSION 3.8)
project(custom_robots)

# Default to C99
if(NOT CMAKE_C_STANDARD)
  set(CMAKE_C_STANDARD 99)
endif()

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ===========================================================================
# find dependencies
set(PROJECT_DEPENDENCIES
  ament_cmake
  rclcpp
  rclpy
  urdf
  xacro
)

foreach(DEPENDENCY ${PROJECT_DEPENDENCIES})
  find_package(${DEPENDENCY} REQUIRED)
endforeach()

# ============================================================================
# Hooks
ament_environment_hooks("hooks/resource_paths.dsv.in")
ament_environment_hooks("hooks/resource_paths.sh")

# ============================================================================
# Resources
install(DIRECTORY
  # TURTLEBOT
  turtlebot2/kobuki_description/launch
  turtlebot2/kobuki_description/meshes
  turtlebot2/kobuki_description/rviz
  turtlebot2/kobuki_description/urdf
  turtlebot2/turtlebot2/launch
  turtlebot2/turtlebot2/rviz
  turtlebot2/turtlebot2/urdf

  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
