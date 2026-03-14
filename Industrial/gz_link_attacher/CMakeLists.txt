cmake_minimum_required(VERSION 3.8)
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

find_package(gz-sim8 REQUIRED)
find_package(gz-plugin2 REQUIRED)

find_package(linkattacher_msgs REQUIRED)

############################
# Plugin library
############################

add_library(gz_link_attacher SHARED
  src/gz_link_attacher.cpp
)

target_link_libraries(gz_link_attacher
  gz-sim8::gz-sim8
  gz-plugin2::gz-plugin2
)

ament_target_dependencies(gz_link_attacher
  rclcpp
  linkattacher_msgs
)

############################
# Install
############################

install(
  TARGETS gz_link_attacher
  LIBRARY DESTINATION lib
)

install(
  TARGETS gz_link_attacher
  LIBRARY DESTINATION /home/drones_ws/install/as2_gazebo_assets/lib
)

############################
# Export
############################

ament_export_libraries(gz_link_attacher)
ament_export_dependencies(
  gz-sim8
  gz-plugin2
)

ament_package()