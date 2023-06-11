cmake_minimum_required(VERSION 3.0.2)
project(drone_assets)

find_package(catkin REQUIRED COMPONENTS gazebo_ros)

find_package(gazebo REQUIRED)

catkin_package()

include_directories(${GAZEBO_INCLUDE_DIRS})

add_library(wall1plugin plugins/wall1.cc)
target_link_libraries(wall1plugin ${catkin_LIBRARIES} ${GAZEBO_LIBRARIES})

add_library(wall2plugin plugins/wall2.cc)
target_link_libraries(wall2plugin ${catkin_LIBRARIES} ${GAZEBO_LIBRARIES})

add_library(wall3plugin plugins/wall3.cc)
target_link_libraries(wall3plugin ${catkin_LIBRARIES} ${GAZEBO_LIBRARIES})

add_library(wall4plugin plugins/wall4.cc)
target_link_libraries(wall4plugin ${catkin_LIBRARIES} ${GAZEBO_LIBRARIES})

install(TARGETS wall1plugin wall2plugin wall3plugin wall4plugin
  LIBRARY DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
)

install(DIRECTORY
  models
  urdf
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
