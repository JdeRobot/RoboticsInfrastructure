cmake_minimum_required(VERSION 3.0.2)
project(dbw_mkz_gui)

find_package(catkin REQUIRED COMPONENTS
  rospy
  rqt_gui
  rqt_gui_py
  dbw_mkz_msgs
)

catkin_python_setup()

catkin_package()

include_directories(
  ${catkin_INCLUDE_DIRS}
)

install(DIRECTORY resource images
        DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)

install(FILES plugin.xml
        DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
