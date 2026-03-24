cmake_minimum_required(VERSION 3.8)
project(gz_noisy_odometry)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(tf2 REQUIRED)

find_package(gz-sim8 REQUIRED)
find_package(gz-plugin2 REQUIRED)
find_package(gz-transport13 REQUIRED)
find_package(gz-msgs10 REQUIRED)
find_package(gz-math7 REQUIRED)

add_library(NoisyOdometryPlugin SHARED
  src/NoisyOdometryPlugin.cpp
)

target_include_directories(NoisyOdometryPlugin PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

ament_target_dependencies(NoisyOdometryPlugin
  rclcpp
  nav_msgs
  tf2
)

target_link_libraries(NoisyOdometryPlugin
  gz-sim8::gz-sim8-system
  gz-plugin2::gz-plugin2-register
  gz-transport13::gz-transport13
  gz-msgs10::gz-msgs10
  gz-math7::gz-math7
)

install(TARGETS NoisyOdometryPlugin
  DESTINATION lib
)

ament_package()