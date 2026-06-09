cmake_minimum_required(VERSION 3.8)
project(conveyor_belt_plugin)

# ============================
# C++ standard
# ============================
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ============================
# Warnings
# ============================
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
# Plugin
# ============================
add_library(conveyor_plugin SHARED
  src/conveyor_plugin.cpp
)

target_include_directories(conveyor_plugin PUBLIC include)

target_link_libraries(conveyor_plugin
  gz-sim8::gz-sim8
  gz-plugin2::gz-plugin2
)

ament_target_dependencies(conveyor_plugin
  rclcpp
)

# ============================
# Install
# ============================
install(TARGETS conveyor_plugin
  LIBRARY DESTINATION lib
)

install(
  FILES env-hooks/conveyor_belt.dsv
  DESTINATION share/${PROJECT_NAME}/environment
)

# ============================
# Export
# ============================
ament_export_libraries(conveyor_plugin)
ament_export_dependencies(gz-sim8 gz-plugin2 rclcpp)

ament_package()