cmake_minimum_required(VERSION 3.10)
project(conveyor_system)

find_package(gz-sim REQUIRED)

add_library(conveyor_system SHARED
  src/conveyor_system.cpp
)

target_link_libraries(conveyor_system
  gz-sim::gz-sim
)

install(TARGETS conveyor_system DESTINATION lib)