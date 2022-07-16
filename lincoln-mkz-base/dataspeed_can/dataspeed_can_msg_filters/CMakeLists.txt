cmake_minimum_required(VERSION 3.0.2)
project(dataspeed_can_msg_filters)

find_package(catkin REQUIRED COMPONENTS
  roscpp
  dataspeed_can_msgs
)

catkin_package(
  INCLUDE_DIRS include
  CATKIN_DEPENDS roscpp dataspeed_can_msgs
)

install(DIRECTORY include/${PROJECT_NAME}/
        DESTINATION ${CATKIN_PACKAGE_INCLUDE_DESTINATION}
)
