cmake_minimum_required(VERSION 4.2.3)
project(gz_noisy_odometry)

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

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(nav_msgs REQUIRED)

find_package(gz-plugin REQUIRED COMPONENTS register)
find_package(gz-sim REQUIRED)
find_package(gz-math REQUIRED)
find_package(gz-common REQUIRED)

# ============================================================================
# Noisy Odometry plugin

add_library(NoisyOdometryPlugin SHARED
  src/gz_noisy_odometry/NoisyOdometryPlugin.cpp
)

target_include_directories(NoisyOdometryPlugin PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

target_link_libraries(NoisyOdometryPlugin
  gz-plugin::gz-plugin
  gz-plugin::register
  gz-sim::gz-sim
  gz-math::gz-math
  gz-common::gz-common
  rclcpp::rclcpp
  nav_msgs::nav_msgs
)

install(
  TARGETS NoisyOdometryPlugin
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(
  DIRECTORY include/
  DESTINATION include
)

ament_export_include_directories(include)
ament_export_libraries(NoisyOdometryPlugin)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  find_package(ament_lint_common REQUIRED)
endif()

ament_package()