cmake_minimum_required(VERSION 3.8)
project(personplugin_harmonic)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)   # si vas a publicar o suscribirte a Twist u otro mensaje
find_package(gz-sim7 REQUIRED)
find_package(gz-plugin2 REQUIRED)
find_package(gz-math7 REQUIRED)
find_package(Threads REQUIRED)

add_library(personplugin_harmonic SHARED src/person_harmonic.cpp)

target_include_directories(personplugin_harmonic
  PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
         $<INSTALL_INTERFACE:include>)

ament_target_dependencies(personplugin_harmonic
  rclcpp
  geometry_msgs
)

target_link_libraries(personplugin_harmonic
  gz-sim8::gz-sim8
  gz-plugin2::gz-plugin2
  gz-math7::gz-math7
  Threads::Threads)

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