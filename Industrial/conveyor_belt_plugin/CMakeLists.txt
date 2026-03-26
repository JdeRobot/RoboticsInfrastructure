cmake_minimum_required(VERSION 3.8)
project(conveyor_belt_plugin)

# ============================
# C++ standard
# ============================
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

# warnings (recomendado)
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ============================
# Dependencies
# ============================
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)

find_package(gz-sim8 REQUIRED)
find_package(gz-plugin2 REQUIRED)

# ============================
# Include directories
# ============================
include_directories(
  include
)

# ============================
# Plugin library
# ============================
add_library(conveyor_plugin SHARED
  src/conveyor_plugin.cpp
)

target_compile_definitions(conveyor_plugin PRIVATE "CONVEYOR_PLUGIN_BUILDING_LIBRARY")

# ============================
# Link libraries
# ============================
target_link_libraries(conveyor_plugin
  gz-sim8::gz-sim8
  gz-plugin2::gz-plugin2
)

# ============================
# ROS2 dependencies
# ============================
ament_target_dependencies(conveyor_plugin
  rclcpp
)

# ============================
# Install plugin
# ============================
install(
  TARGETS conveyor_plugin
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

# ============================
# Environment hook (MUY IMPORTANTE)
# ============================
install(
  FILES env-hooks/conveyor_belt.dsv
  DESTINATION share/${PROJECT_NAME}/environment
)

# ============================
# Export
# ============================
ament_export_libraries(conveyor_plugin)

ament_export_dependencies(
  gz-sim8
  gz-plugin2
  rclcpp
)

# ============================
# Package
# ============================
ament_package()