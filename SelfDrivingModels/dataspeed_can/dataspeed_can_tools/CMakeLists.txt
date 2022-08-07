cmake_minimum_required(VERSION 3.0.2)
project(dataspeed_can_tools)

find_package(catkin REQUIRED COMPONENTS
  rosbag
  roscpp
  roslib
  nodelet
  std_msgs
  dataspeed_can_msgs
)

catkin_package(
  LIBRARIES ${PROJECT_NAME}
)

include_directories(
  ${catkin_INCLUDE_DIRS}
)

add_library(${PROJECT_NAME}
  src/DbcIterator.cpp src/Message.cpp src/Signal.cpp
  src/CanExtractor.cpp
  src/translate_rx_tx_nodelet.cpp
  src/translate_tx_rx_nodelet.cpp
)
add_dependencies(${PROJECT_NAME} dataspeed_can_msgs_gencpp)
target_link_libraries(${PROJECT_NAME}
  ${catkin_LIBRARIES}
)

add_executable(dbc_node src/dbc_node.cpp)
target_link_libraries(dbc_node
  ${PROJECT_NAME}
)

add_executable(dbc_bag src/dbc_bag.cpp)
target_link_libraries(dbc_bag
  ${PROJECT_NAME}
)

add_executable(translate_rx_tx_node src/translate_rx_tx_node.cpp)
add_dependencies(translate_rx_tx_node dataspeed_can_msgs_gencpp)
target_link_libraries(translate_rx_tx_node
  ${catkin_LIBRARIES}
)

add_executable(translate_tx_rx_node src/translate_tx_rx_node.cpp)
add_dependencies(translate_tx_rx_node dataspeed_can_msgs_gencpp)
target_link_libraries(translate_tx_rx_node
  ${catkin_LIBRARIES}
)

install(TARGETS ${PROJECT_NAME} dbc_node dbc_bag translate_rx_tx_node translate_tx_rx_node
        RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
        LIBRARY DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
)
install(FILES nodelets.xml
        DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
