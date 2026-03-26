cmake_minimum_required(VERSION 3.8)
project(conveyor_belt_plugin)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

add_compile_options(-Wall -Wextra -Wpedantic)

# =========================
# Dependencies
# =========================

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)

find_package(gz-sim8 REQUIRED)
find_package(gz-plugin2 REQUIRED)

# =========================
# Plugin
# =========================

add_library(conveyor_system SHARED
  src/conveyor_system.cpp
)

target_link_libraries(conveyor_system
  gz-sim8::gz-sim8
  gz-plugin2::gz-plugin2
)

ament_target_dependencies(conveyor_system
  rclcpp
)

# =========================
# Install
# =========================

install(
  TARGETS conveyor_system
  LIBRARY DESTINATION lib
)

# =========================
# Export
# =========================

ament_export_libraries(conveyor_system)

ament_export_dependencies(
  gz-sim8
  gz-plugin2
)

ament_package()