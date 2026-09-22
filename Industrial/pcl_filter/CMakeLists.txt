cmake_minimum_required(VERSION 4.2.3)
project(pcl_filter)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(std_srvs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(PCL REQUIRED)
find_package(pcl_conversions REQUIRED)
find_package(OpenCV REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(moveit_msgs REQUIRED)
# Custom message dependencies
find_package(pcl_filter_msgs REQUIRED)

include_directories(${PCL_INCLUDE_DIRS})
link_directories(${PCL_LIBRARY_DIRS})
add_definitions(${PCL_DEFINITIONS})

# Create executables
add_executable(pcl_filter_server src/pcl_filter_server.cpp)

target_link_libraries(pcl_filter_server
  rclcpp::rclcpp
  std_srvs::std_srvs
  std_msgs::std_msgs
  geometry_msgs::geometry_msgs
  sensor_msgs::sensor_msgs
  tf2::tf2
  tf2_ros::tf2_ros
  tf2_geometry_msgs::tf2_geometry_msgs
  pcl_conversions::pcl_conversions
  cv_bridge::cv_bridge
  pcl_filter_msgs::pcl_filter_msgs
  moveit_msgs::moveit_msgs
  ${PCL_LIBRARIES} ${OpenCV_LIBS}
)

# Install executables
install(TARGETS
  pcl_filter_server
  DESTINATION lib/${PROJECT_NAME}
)

# Install launch files
install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}/
)

# Install service files
install(DIRECTORY
  srv
  DESTINATION share/${PROJECT_NAME}/
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()