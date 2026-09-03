cmake_minimum_required(VERSION 3.8)
project(gz_bumper)

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

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(nav_msgs REQUIRED)

find_package(gz-plugin2 REQUIRED COMPONENTS register)
find_package(gz-sim8 REQUIRED)
find_package(gz-common5 REQUIRED)
find_package(gz-transport13 REQUIRED)
find_package(gz-msgs10 REQUIRED)
find_package(gz-math7 REQUIRED)

# ============================================================================
# Bumper plugin

add_library(BumperPlugin SHARED
  src/gz_bumper/BumperPlugin.cpp
)

target_include_directories(BumperPlugin PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

ament_target_dependencies(BumperPlugin
  rclcpp
  nav_msgs
)

target_link_libraries(BumperPlugin
  gz-plugin2::gz-plugin2
  gz-plugin2::register
  gz-sim8::gz-sim8
  gz-math7::gz-math7
  gz-transport13::gz-transport13
  gz-common5::gz-common5
  gz-common5::profiler
  gz-msgs10::gz-msgs10
)

install(
  TARGETS BumperPlugin
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(
  DIRECTORY include/
  DESTINATION include
)

ament_export_include_directories(include)
ament_export_libraries(BumperPlugin)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  find_package(ament_lint_common REQUIRED)
endif()

ament_package()