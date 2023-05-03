cmake_minimum_required(VERSION 3.0.2)
project(can_sim_tc)

find_package(catkin REQUIRED COMPONENTS
  rospy
  roscpp
  nodelet
  sensor_msgs
  dataspeed_can_msgs
  dataspeed_can_msg_filters
  dbw_mkz_msgs
  dbw_mkz_can
  geometry_msgs
)

#  Second to make packages work which depend on yours you have to export both include locations
catkin_package(
  LIBRARIES ${PROJECT_NAME}
  INCLUDE_DIRS include
  ${CATKIN_DEVEL_PREFIX}/include
)

include_directories(
  ${catkin_INCLUDE_DIRS}
)

# adds the include dir to compilation
include_directories(include ${CATKIN_DEVEL_PREFIX}/include)

add_library(${PROJECT_NAME}
  src/CanSimTc_nodelet.cpp
  src/CanSimNode.cpp
)
add_dependencies(${PROJECT_NAME} dataspeed_can_msgs_gencpp)
add_dependencies(${PROJECT_NAME} dbw_mkz_msgs_gencpp)
target_link_libraries(${PROJECT_NAME}
  ${catkin_LIBRARIES}
)

add_executable(cansim_node
  src/node.cpp
  src/CanSimNode.cpp
)
add_dependencies(cansim_node dataspeed_can_msgs_gencpp)
add_dependencies(cansim_node dbw_mkz_msgs_gencpp)
target_link_libraries(cansim_node
  ${catkin_LIBRARIES}
)


install(TARGETS ${PROJECT_NAME} cansim_node
        RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
        LIBRARY DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
)
install(DIRECTORY scripts
        DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
        USE_SOURCE_PERMISSIONS
)
install(FILES nodelets.xml
        DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
install(DIRECTORY launch
        DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)

## Install project namespaced headers
install(DIRECTORY include/${PROJECT_NAME}/
  DESTINATION ${CATKIN_PACKAGE_INCLUDE_DESTINATION}
  FILES_MATCHING PATTERN "*.h"
  PATTERN ".svn" EXCLUDE)
