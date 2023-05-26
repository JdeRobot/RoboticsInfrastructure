# Launch physical Turtlebot

Use real Turtlebot2 inside docker:
- Follow kobuki_instructions to build robot's dirvers in your computer 
- Follow rplidar_instructions to build lidar's drivers in ypur computer 
- Launch drivers in your computer and start docker adding the device options to control Serial connection:
    - Kobuki_base: `--dev /dev/kobuki`
    - Rplidar: `--dev /dev/ttyUSBX` check in which X usb is connected with `lsusb`