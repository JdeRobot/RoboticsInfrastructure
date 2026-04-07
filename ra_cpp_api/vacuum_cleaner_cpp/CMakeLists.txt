cmake_minimum_required(VERSION 3.8)
project(vacuum_cleaner_cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(gazebo_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(common_interfaces_cpp REQUIRED)
find_package(Boost REQUIRED COMPONENTS system)
find_package(nlohmann_json REQUIRED)

add_library(${PROJECT_NAME}_lib SHARED
  src/HAL.cpp
  src/Frequency.cpp
  src/WebGUI.cpp
)

target_include_directories(${PROJECT_NAME}_lib PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

target_link_libraries(${PROJECT_NAME}_lib
  Boost::system
  nlohmann_json::nlohmann_json
)

ament_target_dependencies(${PROJECT_NAME}_lib
  rclcpp
  nav_msgs
  gazebo_msgs
  tf2
  tf2_geometry_msgs
  common_interfaces_cpp
)

install(TARGETS ${PROJECT_NAME}_lib
  EXPORT export_${PROJECT_NAME}
  LIBRARY DESTINATION lib
  ARCHIVE DESTINATION lib
  RUNTIME DESTINATION bin
)

install(DIRECTORY include/
  DESTINATION include
)

ament_export_include_directories(include)
ament_export_libraries(${PROJECT_NAME}_lib)
ament_export_targets(export_${PROJECT_NAME})
ament_export_dependencies(
  rclcpp
  nav_msgs
  gazebo_msgs
  tf2
  tf2_geometry_msgs
  common_interfaces_cpp
  Boost
)

ament_package()