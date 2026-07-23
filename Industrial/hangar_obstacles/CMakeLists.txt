cmake_minimum_required(VERSION 3.8)
project(hangar_obstacles)

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

find_package(gz-sim8 REQUIRED)
find_package(gz-plugin2 REQUIRED)

# ============================
# Plugin
# ============================
add_library(hangar_obstacle_mover SHARED
  src/hangar_obstacle_mover.cpp
)

target_link_libraries(hangar_obstacle_mover
  gz-sim8::gz-sim8
  gz-plugin2::gz-plugin2
)

# ============================
# Install
# ============================
install(TARGETS hangar_obstacle_mover
  LIBRARY DESTINATION lib
)

install(
  FILES env-hooks/hangar_obstacles.dsv
  DESTINATION share/${PROJECT_NAME}/environment
)

# ============================
# Export
# ============================
ament_export_libraries(hangar_obstacle_mover)
ament_export_dependencies(gz-sim8 gz-plugin2)

ament_package()
