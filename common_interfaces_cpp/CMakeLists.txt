cmake_minimum_required(VERSION 3.8)
project(common_interfaces_cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

set(ros2_dependencies
  rclcpp
  nav_msgs
  sensor_msgs
  geometry_msgs
  gazebo_msgs
  rosgraph_msgs
  cv_bridge
  ros_gz_interfaces
)

find_package(ament_cmake REQUIRED)

foreach(dependency IN LISTS ros2_dependencies)
  find_package(${dependency} REQUIRED)
endforeach()

find_package(OpenCV REQUIRED)
find_package(Boost REQUIRED COMPONENTS system thread)
find_package(nlohmann_json REQUIRED)

find_package(gz-transport13 REQUIRED)
find_package(gz-msgs10 REQUIRED)

add_library(${PROJECT_NAME} SHARED
  src/hal/bumper.cpp
  src/hal/camera.cpp
  src/hal/classnet.cpp
  src/hal/laser.cpp
  src/hal/lidar.cpp
  src/hal/motors.cpp
  src/hal/odometry.cpp
  src/hal/sim_time.cpp
  src/webgui/WebGUIBridge.cpp
)

target_include_directories(${PROJECT_NAME} PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
  ${OpenCV_INCLUDE_DIRS}
  ${Boost_INCLUDE_DIRS}
)

ament_target_dependencies(${PROJECT_NAME} ${ros2_dependencies})

target_link_libraries(${PROJECT_NAME} 
  ${OpenCV_LIBRARIES}
  Boost::system
  Boost::thread
  nlohmann_json::nlohmann_json
  gz-transport13::core
  gz-msgs10::gz-msgs10
)

install(DIRECTORY include/ DESTINATION include)

install(TARGETS ${PROJECT_NAME}
  EXPORT ${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

ament_export_include_directories(include)
ament_export_targets(${PROJECT_NAME} HAS_LIBRARY_TARGET)
ament_export_dependencies(
  ${ros2_dependencies} 
  OpenCV 
  nlohmann_json 
  Boost 
  gz-transport13 
  gz-msgs10
)

ament_package()