##############################################################################
# CMake
##############################################################################

cmake_minimum_required(VERSION 3.5)
project(kobuki_ros_interfaces)

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

##############################################################################
# Dependencies
##############################################################################

find_package(action_msgs REQUIRED)
find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)

##############################################################################
# Messages
##############################################################################

set(msg_files
    "msg/BumperEvent.msg"
    "msg/CliffEvent.msg"
    "msg/DigitalOutput.msg"
    "msg/ExternalPower.msg"
    "msg/Led.msg"
    "msg/PowerSystemEvent.msg"
    "msg/SensorState.msg"
    "msg/VersionInfo.msg"
    "msg/ControllerInfo.msg"
    "msg/ButtonEvent.msg"
    "msg/DigitalInputEvent.msg"
    "msg/DockInfraRed.msg"
    "msg/KeyboardInput.msg"
    "msg/MotorPower.msg"
    "msg/RobotStateEvent.msg"
    "msg/Sound.msg"
    "msg/ScanAngle.msg"
    "msg/WheelDropEvent.msg"
)   

set(action_files
    "action/AutoDocking.action"
)

rosidl_generate_interfaces(${PROJECT_NAME}
  ${msg_files}
  ${action_files}
  DEPENDENCIES
    action_msgs  # even though not directly using, it requires some trace back
    std_msgs
  # ADD_LINTER_TESTS  # very expensive
)
##############################################################################
# Package
##############################################################################

ament_export_dependencies(rosidl_default_runtime)

ament_package()
