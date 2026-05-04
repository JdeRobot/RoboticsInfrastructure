cmake_minimum_required(VERSION 3.8)
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

find_package(gz-sim8 REQUIRED)
find_package(gz-plugin2 REQUIRED)


############################
# Plugin library
############################

add_library(gz_mimic_joint SHARED
  src/gz_mimic_joint.cpp
)

target_link_libraries(gz_mimic_joint
  gz-sim8::gz-sim8
  gz-plugin2::gz-plugin2
)

ament_target_dependencies(gz_mimic_joint
  rclcpp
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
  gz-sim8
  gz-plugin2
)

ament_package()