cmake_minimum_required(VERSION 3.8)
project(dobot_magician_kinematics_plugin)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(moveit_core REQUIRED)
find_package(pluginlib REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(moveit_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)

add_library(dobot_magician_kinematics_plugin SHARED
  src/dobot_magician_kinematics_plugin.cpp
)

target_include_directories(dobot_magician_kinematics_plugin PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

ament_target_dependencies(dobot_magician_kinematics_plugin
  rclcpp
  moveit_core
  pluginlib
  geometry_msgs
  moveit_msgs
  tf2
  tf2_geometry_msgs
)

pluginlib_export_plugin_description_file(moveit_core dobot_magician_kinematics_description.xml)

install(
  TARGETS dobot_magician_kinematics_plugin
  LIBRARY DESTINATION lib
  ARCHIVE DESTINATION lib
  RUNTIME DESTINATION bin
)

install(
  DIRECTORY include/
  DESTINATION include
)

install(
  FILES dobot_magician_kinematics_description.xml
  DESTINATION share/${PROJECT_NAME}
)

ament_export_include_directories(include)
ament_export_libraries(dobot_magician_kinematics_plugin)
ament_export_dependencies(rclcpp moveit_core pluginlib geometry_msgs moveit_msgs tf2 tf2_geometry_msgs)

ament_package()
