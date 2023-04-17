cmake_minimum_required(VERSION 3.8)
project(custom_robots)

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
set(PROJECT_DEPENDENCIES
  ament_cmake
  sensor_msgs
  rclcpp
  rclpy
  urdf
  xacro
  ament_cmake_ros
  gazebo
  pluginlib
  Threads
)

foreach(DEPENDENCY ${PROJECT_DEPENDENCIES})
  find_package(${DEPENDENCY} REQUIRED)
endforeach()


# ============================================================================
# Person plugin
if(CMAKE_USE_PTHREADS_INIT)
  set(CMAKE_C_FLAGS ${CMAKE_C_FLAGS} "-pthread")
endif()

include_directories(${GAZEBO_INCLUDE_DIRS})

add_library(personplugin amazon_hospital/src/person.cpp)
target_include_directories(personplugin PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
ament_target_dependencies(
  personplugin
  "rclcpp"
  "gazebo"
  "pluginlib"
)

# Causes the visibility macros to use dllexport rather than dllimport,
# which is appropriate when building the dll but not consuming it.
target_compile_definitions(personplugin PRIVATE "PERSONPLUGIN_BUILDING_LIBRARY")

install(
  TARGETS personplugin
  EXPORT export_${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

# ============================================================================
# Hooks
ament_environment_hooks("hooks/resource_paths.dsv.in")
ament_environment_hooks("hooks/resource_paths.sh")

# ============================================================================
# Resources
install(DIRECTORY
  # TURTLEBOT
  turtlebot2/kobuki_description/launch
  turtlebot2/kobuki_description/meshes
  turtlebot2/kobuki_description/rviz
  turtlebot2/kobuki_description/urdf
  turtlebot2/turtlebot2/launch
  turtlebot2/turtlebot2/rviz
  turtlebot2/turtlebot2/urdf

  DESTINATION share/${PROJECT_NAME}
)

install(DIRECTORY
  # ROOMBA
  roomba_robot/roombaROS/meshes
  roomba_robot/roombaROS/materials

  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()


ament_export_libraries(
  personplugin
)

ament_export_targets(
  export_${PROJECT_NAME}
)

ament_package()
