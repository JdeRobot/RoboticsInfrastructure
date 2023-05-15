# Platform controller for amazon_robot model

- 1. Launch model inside a scenary with any launcher inside launch directory; custom_robots package must be built for launchers to work porperly.
- 2. Build this package and source `/install` directory from workspace root:
    >> colcon build --symlink-install --packages-select platform_controller
    
    >> . install/setup.bash
- 3. Run platform controller node:
    >> ros2 run platform_controller move_platform
- 4. Sent a command to the controllr by publishing a message:
    
    LOAD MESSAGE (lift up platform):
    >> ros2 topic pub --once  /send_effort std_msgs/String "data: load"

    UNLOAD MESSAGE (move down platform):
    >> ros2 topic pub --once  /send_effort std_msgs/String "data: unload"


    