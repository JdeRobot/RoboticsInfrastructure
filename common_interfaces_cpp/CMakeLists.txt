cmake_minimum_required(VERSION 3.8)
project(common_interfaces_cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Define a list of dependencies for easy modularity and future additions
set(DEPENDENCIES
  rclcpp
  sensor_msgs
  nav_msgs
  geometry_msgs
)

# Find ament_cmake (required for the build system itself)
find_package(ament_cmake REQUIRED)

# Loop through the list to find all specified packages automatically
foreach(dependency IN LISTS DEPENDENCIES)
  find_package(${dependency} REQUIRED)
endforeach()

# Create the shared library from the source files
add_library(${PROJECT_NAME} SHARED
  laser.cpp
  lidar.cpp
  motors.cpp
  odometry.cpp
)

# Link all listed dependencies to the library
ament_target_dependencies(${PROJECT_NAME} ${DEPENDENCIES})

# Install the library so other packages in the workspace can use it
install(TARGETS ${PROJECT_NAME}
  EXPORT ${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)
# Export all listed dependencies for downstream packages
ament_export_dependencies(${DEPENDENCIES})
ament_export_targets(${PROJECT_NAME} HAS_LIBRARY_TARGET)

ament_package()