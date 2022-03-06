# Turtlebot 2 (ROS Foxy version)
## Introduction
This is a version exported to ROS Foxy of Turtlebot 2. The robot has built-in 2 sensors that can be removed or placed by the user through the file **./turtlebot2/urdf/turtlebot2.urdf.xacro**:

* A RGBD simulated camera to obtain a **PointCloud** of the scene captured in every moment.
* A 360º simulated LIDAR to obtain the distance with the obstacles around the robot.

![](https://github.com/JdeRobot/CustomRobots/blob/foxy-devel/turtlebot2/turtlebot2-sim.png)

## Usage
Once the repository is compiled, you will have to execute the following commands (each command in a different terminal and the last is optional):
~~~
ros2 launch turtlebot2 empty_world.launch.py
ros2 launch turtlebot2 spawn_model.launch.py
ros2 launch kobuki_keyop kobuki_keyop.launch.py
~~~

