cmake_minimum_required(VERSION 3.10)
project(gz_map_creator)

# Default to C++17
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find ROS2 dependencies
find_package(ament_cmake REQUIRED)
find_package(nav_msgs REQUIRED)

# ============================================================================
# Find Gazebo Sim packages
# Ignition Fortress uses "ignition-gazebo6" naming
# Newer versions use "gz-sim7" or "gz-sim8" naming
# ============================================================================

# Try gz-sim (newer naming) first
find_package(gz-sim8 QUIET)
if(gz-sim8_FOUND)
  set(GZ_SIM_VER 8)
  set(GZ_PREFIX "gz")
  message(STATUS "Found gz-sim8 (Gazebo Harmonic)")
endif()

if(NOT GZ_SIM_VER)
  find_package(gz-sim7 QUIET)
  if(gz-sim7_FOUND)
    set(GZ_SIM_VER 7)
    set(GZ_PREFIX "gz")
    message(STATUS "Found gz-sim7 (Gazebo Garden)")
  endif()
endif()


if(NOT GZ_SIM_VER)
  message(FATAL_ERROR "No Gazebo Sim package found! Tried gz-sim8, gz-sim7, ignition-gazebo6")
endif()

# Find related packages based on what version we found
if(GZ_PREFIX STREQUAL "gz")
  # Newer gz naming
  if(GZ_SIM_VER EQUAL 8)
    find_package(gz-plugin2 REQUIRED)
    find_package(gz-transport13 QUIET)
    if(NOT gz-transport13_FOUND)
      find_package(gz-transport12 REQUIRED)
      set(GZ_TRANSPORT_VER 12)
    else()
      set(GZ_TRANSPORT_VER 13)
    endif()
    find_package(gz-msgs10 QUIET)
    if(NOT gz-msgs10_FOUND)
      find_package(gz-msgs9 REQUIRED)
      set(GZ_MSGS_VER 9)
    else()
      set(GZ_MSGS_VER 10)
    endif()
    find_package(gz-math7 REQUIRED)
    find_package(gz-common5 REQUIRED)
    set(GZ_PLUGIN_VER 2)
    set(GZ_MATH_VER 7)
    set(GZ_COMMON_VER 5)
  elseif(GZ_SIM_VER EQUAL 7)
    find_package(gz-plugin2 REQUIRED)
    find_package(gz-transport12 REQUIRED)
    find_package(gz-msgs9 REQUIRED)
    find_package(gz-math7 REQUIRED)
    find_package(gz-common5 REQUIRED)
    set(GZ_PLUGIN_VER 2)
    set(GZ_TRANSPORT_VER 12)
    set(GZ_MSGS_VER 9)
    set(GZ_MATH_VER 7)
    set(GZ_COMMON_VER 5)
  endif()
endif()

message(STATUS "Using ${GZ_PREFIX} packages: sim${GZ_SIM_VER}, plugin${GZ_PLUGIN_VER}, transport${GZ_TRANSPORT_VER}, msgs${GZ_MSGS_VER}, math${GZ_MATH_VER}")

# Include directories
include_directories(include)

# Build the Gazebo Fortress system plugin
add_library(gz_2Dmap_system SHARED
  src/gz_2Dmap_system.cc
)

# Link against packages based on naming convention
if(GZ_PREFIX STREQUAL "gz")
  target_link_libraries(gz_2Dmap_system
    gz-sim${GZ_SIM_VER}::gz-sim${GZ_SIM_VER}
    gz-plugin${GZ_PLUGIN_VER}::gz-plugin${GZ_PLUGIN_VER}
    gz-transport${GZ_TRANSPORT_VER}::gz-transport${GZ_TRANSPORT_VER}
    gz-msgs${GZ_MSGS_VER}::gz-msgs${GZ_MSGS_VER}
    gz-math${GZ_MATH_VER}::gz-math${GZ_MATH_VER}
    gz-common${GZ_COMMON_VER}::gz-common${GZ_COMMON_VER}
  )
endif()

# Install the plugin library
install(TARGETS gz_2Dmap_system
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

# Install headers
install(DIRECTORY include/
  DESTINATION include
  FILES_MATCHING PATTERN "*.hh"
)

# Install scripts
install(PROGRAMS scripts/generate_map.sh
  DESTINATION lib/${PROJECT_NAME}
)

# Install launch files if they exist
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/launch")
  install(DIRECTORY launch/
    DESTINATION share/${PROJECT_NAME}/launch
  )
endif()

# Install world files if they exist
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/worlds")
  install(DIRECTORY worlds/
    DESTINATION share/${PROJECT_NAME}/worlds
  )
endif()

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

# Export package information
ament_package()