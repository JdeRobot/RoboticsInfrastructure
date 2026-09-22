cmake_minimum_required(VERSION 4.2.3)
project(gz_mimic_joint)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

############################
# Dependencies
############################

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)

find_package(gz-sim REQUIRED)
find_package(gz-plugin REQUIRED)


############################
# Plugin library
############################

add_library(gz_mimic_joint SHARED
  src/gz_mimic_joint.cpp
)

target_link_libraries(gz_mimic_joint
  rclcpp::rclcpp
  gz-sim::gz-sim
  gz-plugin::gz-plugin
)

############################
# Install plugin
############################

install(
  TARGETS gz_mimic_joint
  LIBRARY DESTINATION lib
)

############################
# Environment hook (.dsv)
############################

install(
  FILES env-hooks/gz_mimic_joint.dsv
  DESTINATION share/${PROJECT_NAME}/environment
)

############################
# Export
############################

ament_export_libraries(gz_mimic_joint)

ament_export_dependencies(
  gz-sim
  gz-plugin
)

ament_package()