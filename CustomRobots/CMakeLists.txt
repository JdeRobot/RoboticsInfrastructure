cmake_minimum_required(VERSION 3.8)
project(custom_robots)

# Define project root directory
set(RI_ROOT_DIR ${CMAKE_CURRENT_SOURCE_DIR}/..)

# Default to C99
if(NOT CMAKE_C_STANDARD)
  set(CMAKE_C_STANDARD 99)
endif()

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ===========================================================================
# find dependencies
set(PROJECT_DEPENDENCIES
    ament_cmake
    sensor_msgs
    rclcpp
    rclpy
    urdf
    xacro
    ament_cmake_ros
    pluginlib
    Threads)

foreach(dependency ${PROJECT_DEPENDENCIES})
  find_package(${dependency} REQUIRED)
endforeach()

add_subdirectory(follow_person_harmonic)

# ============================================================================
# Person plugin
if(CMAKE_USE_PTHREADS_INIT)
  set(CMAKE_C_FLAGS ${CMAKE_C_FLAGS} "-pthread")
endif()

include_directories(${GAZEBO_INCLUDE_DIRS})

# ============================================================================
# Hooks
ament_environment_hooks("hooks/resource_paths.dsv.in")
ament_environment_hooks("hooks/resource_paths.sh")

# ============================================================================
# Resources
install(
  DIRECTORY
    follow_person_harmonic/models
    
    f1/models
    f1/params
    f1/launch

    autonomous_car/models
    autonomous_car/params
    autonomous_car/launch

    vacuum_cleaner/models
    vacuum_cleaner/params
    vacuum_cleaner/launch

    quadrotor/models
    quadrotor/params
    quadrotor/launch

    dingo/model
    dingo/params
    dingo/launch

    rover_4wd/model
    rover_4wd/params
    rover_4wd/launch

    Turtlebot2/model
    Turtlebot2/params
    Turtlebot2/launch

    turtlebot3/models
    turtlebot3/params
    turtlebot3/launch

    logistic_holonomic_robot/models
    logistic_holonomic_robot/params
    logistic_holonomic_robot/launch

    logistic_ackermann_robot/models
    logistic_ackermann_robot/params
    logistic_ackermann_robot/launch

    robot_arms/launch
    robot_arms/models
    robot_arms/config

    roomba_robot/models

    car_junction/models
    car_junction/scripts

    amazon_warehouse_harmonic/models

    package_delivery/models

    # AMAZON HOSPITAL
    amazon_hospital/models

    autopark_harmonic/models

    drone_assets/models
    drone_assets/bridges

    # drone cat-mouse city model (my_city_v3); its bridge yaml lives in
    # drone_assets/bridges above
    drone_cat_mouse/models

    taxi_navigator/models
    
    3d_reconstruction/models
    
    marker_visual_loc/models

    turtlebot3/urdf

    laser_mapping/models

    restaurant/models
    
    pick_place/models

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

ament_package()