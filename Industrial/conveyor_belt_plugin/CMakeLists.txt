cmake_minimum_required(VERSION 3.8)
project(conveyor_belt_plugin)

find_package(gz-sim REQUIRED)

add_library(conveyor_plugin SHARED
  src/conveyor_plugin.cpp
)

target_link_libraries(conveyor_plugin
  gz-sim::gz-sim
)

install(TARGETS conveyor_plugin
  LIBRARY DESTINATION lib
)