# JdeRobot - Custom Robots

In this JdeRobot repository we structure the formula 1 related robots, Amazon warehouse robots and all specific robots useful for us and not included in the official ROS or Gazebo packages.

## How to contribute.

**First of all** you have to know the infrastructure where you will develop your code: 

- Gazebo version,
- ROS version
- Python version (if you develop in Python).

This repository is divided into **four branches**. **Depending on the version** of the mentioned software you will have to move to one of them to have the version compatible with your software. The branches are:
- `melodic-devel` (default branch)
- [`noetic-devel`](https://github.com/JdeRobot/CustomRobots/tree/noetic-devel)
- [`foxy-devel`](https://github.com/JdeRobot/CustomRobots/tree/foxy-devel)
- [`humble-devel`](https://github.com/JdeRobot/CustomRobots/tree/humble-devel)

## HUMBLE
To create a docker container with ROS2-humble first pull the RADI image with `docker pull jderobot/robotics-academy:4.3.X` and run:
~~~
 cd scripts && ./run.sh  <----- starts RAM automatically
~~~

Enter the container with a different configuration with:
~~~
./run.sh -d      <-----
./run.sh --debug <----- open a terminal inside container
./run.sh -v <absolute_local_route>        <----- create a shared directory between local 
./run.sh --volume <absolute_local_route>  <----- host and container in /home/shared_dir
./run.sh -n <container_name>     <-----
./run.sh --name <container_name> <----- stablish the container name (default is: dockerRam_container)
./run.sh --dev <name of card> <----- enable GPU acceleration (name of device must be specified)
~~~
Run RADI inside the container with:
~~~
 ./entrypoint.sh
~~~

### Example of usage:
~~~
./run.sh -v /home/user/directory -n my_container --dev card0 -d
~~~
