cmake_minimum_required(VERSION 3.8)
project(waypoint_follower_harmonic)

find_package(gz-sim8 REQUIRED)
find_package(gz-plugin2 REQUIRED)
find_package(gz-math7 REQUIRED)

add_library(waypoint_follower_harmonic SHARED src/waypoint_follower.cpp)

set_target_properties(waypoint_follower_harmonic PROPERTIES
  CXX_STANDARD 17
  CXX_STANDARD_REQUIRED ON)

target_link_libraries(waypoint_follower_harmonic
  gz-sim8::gz-sim8
  gz-plugin2::gz-plugin2
  gz-math7::gz-math7)

install(
  TARGETS waypoint_follower_harmonic
  LIBRARY DESTINATION lib
)
