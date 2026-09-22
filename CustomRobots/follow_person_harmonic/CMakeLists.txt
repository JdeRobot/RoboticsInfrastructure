cmake_minimum_required(VERSION 4.2.3)
project(personplugin_harmonic)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)   # si vas a publicar o suscribirte a Twist u otro mensaje
find_package(gz-sim REQUIRED)
find_package(gz-plugin REQUIRED)
find_package(gz-math REQUIRED)
find_package(Threads REQUIRED)

add_library(personplugin_harmonic SHARED src/person_harmonic.cpp)

target_include_directories(personplugin_harmonic
  PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
         $<INSTALL_INTERFACE:include>)

target_link_libraries(personplugin_harmonic
  gz-sim::gz-sim
  gz-plugin::gz-plugin
  gz-math::gz-math
  Threads::Threads
  rclcpp::rclcpp
  geometry_msgs::geometry_msgs
)

target_compile_definitions(personplugin_harmonic PRIVATE "PERSONPLUGIN_BUILDING_LIBRARY")

install(
  TARGETS personplugin_harmonic
  EXPORT export_${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

ament_export_libraries(personplugin_harmonic)
ament_export_targets(export_${PROJECT_NAME})
ament_package()