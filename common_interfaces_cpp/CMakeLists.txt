cmake_minimum_required(VERSION 3.8)
project(common_interfaces_cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Define a list of ROS 2 dependencies for easy modularity
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

# Loop through the list to find all specified ROS 2 packages automatically
foreach(dependency IN LISTS ros2_dependencies)
  find_package(${dependency} REQUIRED)
endforeach()

# Find OpenCV explicitly (Required by Camera and Classnet for cv::Mat and cv::dnn)
find_package(OpenCV REQUIRED)

# Find external C++ libraries for the WebGUI
find_package(Boost REQUIRED COMPONENTS system thread)
find_package(nlohmann_json REQUIRED)

# Create the shared library from the source files matching the new structure
add_library(${PROJECT_NAME} SHARED
  # HAL
  src/hal/bumper.cpp
  src/hal/camera.cpp
  src/hal/classnet.cpp
  src/hal/laser.cpp
  src/hal/lidar.cpp
  src/hal/motors.cpp
  src/hal/odometry.cpp
  src/hal/sim_time.cpp
  # WebGUI
  src/webgui/MeasuringThreadingGUI.cpp
)

# Specify the include directories so the compiler finds the .hpp files
target_include_directories(${PROJECT_NAME} PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
  ${OpenCV_INCLUDE_DIRS}
  ${Boost_INCLUDE_DIRS}
)

# Link all listed ROS 2 dependencies and OpenCV to the library
ament_target_dependencies(${PROJECT_NAME} ${ros2_dependencies})
target_link_libraries(${PROJECT_NAME} 
  ${OpenCV_LIBRARIES}
  Boost::system
  Boost::thread
  nlohmann_json::nlohmann_json
)

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