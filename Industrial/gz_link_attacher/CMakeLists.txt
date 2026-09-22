cmake_minimum_required(VERSION 4.2.3)
project(gz_link_attacher)

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
find_package(std_msgs REQUIRED)

find_package(gz-sim REQUIRED)
find_package(gz-plugin REQUIRED)

find_package(linkattacher_msgs REQUIRED)

############################
# Plugin library
############################

add_library(gz_link_attacher SHARED
  src/gz_link_attacher.cpp
)

target_link_libraries(gz_link_attacher
  rclcpp::rclcpp
  gz-sim::gz-sim
  gz-plugin::gz-plugin
  std_msgs::std_msgs
)

############################
# Install plugin
############################

install(
  TARGETS gz_link_attacher
  LIBRARY DESTINATION lib
)

############################
# Environment hook (.dsv)
############################

install(
  FILES env-hooks/gz_link_attacher.dsv
  DESTINATION share/${PROJECT_NAME}/environment
)

############################
# Export
############################

ament_export_libraries(gz_link_attacher)

ament_export_dependencies(
  gz-sim
  gz-plugin
)

ament_package()