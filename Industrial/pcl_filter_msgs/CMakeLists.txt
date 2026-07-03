cmake_minimum_required(VERSION 3.8)
project(pcl_filter_msgs)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# Generate messages
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/ColorFilter.msg"
  "msg/ShapeFilter.msg"
)

# Export dependencies
ament_export_dependencies(rosidl_default_runtime)

# This is important for other packages to find the generated headers
rosidl_get_typesupport_target(cpp_typesupport_target ${PROJECT_NAME} "rosidl_typesupport_cpp")

ament_package()