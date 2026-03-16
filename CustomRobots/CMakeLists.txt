cmake_minimum_required(VERSION 3.8)
project(custom_robots)

set(RI_ROOT_DIR ${CMAKE_CURRENT_SOURCE_DIR}/..)

if(NOT CMAKE_C_STANDARD)
  set(CMAKE_C_STANDARD 99)
endif()

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

set(PROJECT_DEPENDENCIES
    ament_cmake
    sensor_msgs
    rclcpp
    rclpy
    urdf
    xacro
    ament_cmake_ros
    #gazebo
    pluginlib
    Threads)

foreach(dependency ${PROJECT_DEPENDENCIES})
  find_package(${dependency} REQUIRED)
endforeach()

# -------------------
# Classic
find_package(gazebo REQUIRED)
include_directories(${GAZEBO_INCLUDE_DIRS})

# Compilamos objetos primero para evitar conflictos con JsonCpp
add_library(personplugin_obj OBJECT amazon_hospital/src/person.cpp)
target_include_directories(personplugin_obj
  PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
         $<INSTALL_INTERFACE:include>)
target_compile_definitions(personplugin_obj PRIVATE "PERSONPLUGIN_BUILDING_LIBRARY")

# Ahora creamos la librería final Classic
add_library(personplugin STATIC $<TARGET_OBJECTS:personplugin_obj>)
target_link_libraries(personplugin Threads::Threads)
target_include_directories(personplugin
  PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
         $<INSTALL_INTERFACE:include>)

ament_target_dependencies(personplugin "rclcpp" "pluginlib" "gazebo")

# -------------------
# Harmonic / Ignition
find_package(gz-sim8 REQUIRED)
find_package(gz-plugin2 REQUIRED)
find_package(gz-math7 REQUIRED)

add_library(personplugin_harmonic follow_person_harmonic/src/person_harmonic.cpp)
target_include_directories(personplugin_harmonic
  PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
         $<INSTALL_INTERFACE:include>)
ament_target_dependencies(personplugin_harmonic "rclcpp" "pluginlib")
target_link_libraries(personplugin_harmonic
  gz-sim8::gz-sim8
  gz-plugin2::gz-plugin2
  gz-math7::gz-math7
  Threads::Threads)
target_compile_definitions(personplugin_harmonic PRIVATE "PERSONPLUGIN_BUILDING_LIBRARY")

# -------------------
# Instalación de librerías
install(
  TARGETS personplugin personplugin_harmonic
  EXPORT export_${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin)

ament_environment_hooks("hooks/resource_paths.dsv.in")
ament_environment_hooks("hooks/resource_paths.sh")

install(
  DIRECTORY
    follow_person_harmonic/models
    follow_person_harmonic/params
    Turtlebot2/turtlebot2_simulated/kobuki_description/launch
    Turtlebot2/turtlebot2_simulated/kobuki_description/meshes
    Turtlebot2/turtlebot2_simulated/kobuki_description/rviz
    Turtlebot2/turtlebot2_simulated/kobuki_description/urdf
    Turtlebot2/turtlebot2_simulated/turtlebot2/launch
    Turtlebot2/turtlebot2_simulated/turtlebot2/rviz
    Turtlebot2/turtlebot2_simulated/turtlebot2/urdf
    f1/models
    f1/params
    roomba_robot/models
    roomba_robot/params
    ackermann_cars/models
    ackermann_cars/params
    car_junction/models
    car_junction/scripts
    # AMAZON WAREHOUSE ROBOT
    amazon_robot_classic/models
    amazon_robot_classic/urdf
    amazon_robot_classic/meshes
    amazon_warehouse_harmonic/models
    amazon_warehouse_harmonic/params
    # AMAZON HOSPITAL
    amazon_hospital/models
    amazon_hospital/hospital_world/launch
    amazon_hospital/hospital_world/worlds
    amazon_hospital/worlds
    ackermann_logistic_robot/models
    autoparking/models
    autopark_harmonic/models
    autopark_harmonic/params
    drone_assets/models
    drone_assets/worlds
    drone_assets/bridges
    taxi_navigator/models
    taxi_navigator/params
    3d_reconstruction/models
    3d_reconstruction/params
    marker_visual_loc/models
    turtlebot3/models
    turtlebot3/urdf
    turtlebot3/params
    laser_mapping/models
    restaurant/models
    pick_place/models
    pick_place/urdf
    rover_4wd_description/meshes
    rover_4wd_description/urdf
    rover_4wd_description/config
  DESTINATION share/${PROJECT_NAME})

# install(
#   FILES ${RI_ROOT_DIR}/Launchers/follow_road.launch.py
#         ${RI_ROOT_DIR}/Launchers/rescue_people.launch.py
#   DESTINATION share/${PROJECT_NAME}/launch)

if(BUILD_TESTING)
  # find_package(ament_lint_auto REQUIRED)
  # ament_lint_auto_find_test_dependencies()

  # find_package(launch_testing_ament_cmake REQUIRED)
  # # Use file(GLOB...) to find all test files matching the pattern
  # file(GLOB TEST_FILES "${RI_ROOT_DIR}/test/test*.py")
  # # Loop through each test file and add it as a launch test
  # foreach(test_file ${TEST_FILES})
  #   add_launch_test(${test_file} TIMEOUT 90)
  # endforeach()
endif()

ament_export_libraries(personplugin_harmonic) #personplugin

ament_export_targets(export_${PROJECT_NAME})

ament_package()