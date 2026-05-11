cmake_minimum_required(VERSION 3.8)
project(jderobot_drones_cpp)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

set(CMAKE_POSITION_INDEPENDENT_CODE ON)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(as2_core REQUIRED)
find_package(as2_msgs REQUIRED)
find_package(as2_motion_reference_handlers REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(image_transport REQUIRED)
find_package(OpenCV REQUIRED)
find_package(std_srvs REQUIRED)

include_directories(include)

add_library(drone_lib_cpp SHARED src/drone_wrapper.cpp src/image_sub.cpp)

ament_target_dependencies(drone_lib_cpp 
    rclcpp as2_core as2_msgs as2_motion_reference_handlers 
    geometry_msgs sensor_msgs std_srvs cv_bridge image_transport OpenCV)

install(TARGETS drone_lib_cpp
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(DIRECTORY include/ DESTINATION include)
install(DIRECTORY launch sim_config DESTINATION share/${PROJECT_NAME})

ament_export_include_directories(include)
ament_export_libraries(drone_lib_cpp)
ament_package()