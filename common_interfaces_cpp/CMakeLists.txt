cmake_minimum_required(VERSION 3.8)
project(common_interfaces_cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Define a list of dependencies for easy modularity and future additions
set(ros2_dependencies
  rclcpp
  nav_msgs
)

# Find ament_cmake (required for the build system itself)
find_package(ament_cmake REQUIRED)

# Loop through the list to find all specified packages automatically
foreach(dependency IN LISTS ros2_dependencies)
  find_package(${dependency} REQUIRED)
endforeach()

# Create the shared library from the source files
add_library(${PROJECT_NAME} SHARED
  src/odometry.cpp
)

# Specify the include directories so the compiler finds the .hpp files
target_include_directories(${PROJECT_NAME} PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

# Link all listed dependencies to the library
ament_target_dependencies(${PROJECT_NAME} ${ros2_dependencies})

# Install the include directory so other packages can do #include
install(DIRECTORY include/
  DESTINATION include
)

# Install the library and export the target for downstream usage
install(TARGETS ${PROJECT_NAME}
  EXPORT ${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

# Export include directories, targets, and dependencies
ament_export_include_directories(include)
ament_export_targets(${PROJECT_NAME} HAS_LIBRARY_TARGET)
ament_export_dependencies(${ros2_dependencies})

ament_package()