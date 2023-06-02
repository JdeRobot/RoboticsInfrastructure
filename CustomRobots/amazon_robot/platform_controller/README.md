# Platform controller for amazon_robot model

## TRY CONTROLLER
Setup the environment to test the platform controller with `try_controller.sh` script. This script will launch a vnc server in port localhost:6080, build this package, launch scenary with amazon robot and warehouse and run controller. After executing this script you can send topic messages as the ones on step 4 (below indicated) to move robot's platform.  

## STEP BY STEP
- 1. Launch model inside a scenary with any launcher inside `amazon_robot/launch` directory; custom_robots package must be built for launchers to work porperly.
- 2. Build this package and source `/install` directory from workspace root:
    > colcon build --symlink-install --packages-select platform_controller
    
    > . install/setup.bash
- 3. Run platform controller node:
    > ros2 run platform_controller move_platform
- 4. Send a command to the controller by publishing a message:
    
    LOAD MESSAGE (lift up platform):
    > ros2 topic pub --once  /send_effort std_msgs/String "data: load"

    UNLOAD MESSAGE (move down platform):
    > ros2 topic pub --once  /send_effort std_msgs/String "data: unload"
    
