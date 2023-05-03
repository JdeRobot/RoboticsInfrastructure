cmake_minimum_required(VERSION 3.0.2)
project(dbw_mkz_joystick_demo)

set(${PROJECT_NAME}_CATKIN_DEPS
  roscpp
  dbw_mkz_msgs
)

find_package(catkin REQUIRED COMPONENTS ${${PROJECT_NAME}_CATKIN_DEPS})

catkin_package()

include_directories(
  ${catkin_INCLUDE_DIRS}
)

add_executable(joystick_demo src/joystick_demo.cpp src/JoystickDemo.cpp)
add_dependencies(joystick_demo dbw_mkz_msgs_gencpp)
target_link_libraries(joystick_demo
  ${catkin_LIBRARIES}
)

install(TARGETS joystick_demo
        RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch
        DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
