# Turtlebot2 Simulated for ROS Humble

The original model was done for ROS Foxy (can be found [there](https://github.com/RoboticsLabURJC/2021-tfg-carlos-caminero/tree/main/turtlebot2)) but can be reused for ROS Humble.

## Drivers 
The robot includes
* Kobuki motor base
* a RGBD webcam
* a RPLidar laser sensor


## Usage
Launch the world (empty world, hospital...) in a terminal. For example, to launch the empty world
~~~
ros2 launch gazebo_ros gazebo.launch.py
~~~

Then, launch the robot in another terminal
~~~
ros2 launch turtlebot2 spawn_model.launch.py
~~~

## Issues
If after launching the robot only the upper part appears and not the kobuki base, please change the path of the wheels and base to an absolute path (lines 28, 62 and 87 of the turtlebot2.urdf file located in /turtlebot2/urdf).

