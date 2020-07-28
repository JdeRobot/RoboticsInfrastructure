cmake_minimum_required(VERSION 3.0.2)
project(jderobot_assets)

## ROS INSTALL ##

find_package(catkin REQUIRED COMPONENTS)

catkin_package()

install(DIRECTORY models worlds
 DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)

## JDEROBOT INSTALL ##

if (CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)
    set (CMAKE_INSTALL_PREFIX /opt/jderobot/share/jderobot/
         CACHE PATH "default install path" FORCE)
endif()

set (MODELS ${CMAKE_INSTALL_PREFIX}/gazebo/models)
set (WORLDS ${CMAKE_INSTALL_PREFIX}/gazebo/worlds)

configure_file (
    assets-setup.sh.in
    assets-setup.sh
)

install(DIRECTORY models worlds launch
DESTINATION gazebo)
install(FILES ${CMAKE_CURRENT_BINARY_DIR}/assets-setup.sh 
DESTINATION gazebo)


include(cpackit.cmake)
