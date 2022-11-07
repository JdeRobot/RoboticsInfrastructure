# Physical Turtlebot2

## Setup Kobuki base

1. Connect the Kobuki to your laptop by USB (**Switch On the robot**)
2. Check that the device has `rw` permission for `dialout` group, and you are in this group

```
ls /dev/ttyUSB0
id
```

If you are not in `dialout` group, add yourself to this group:

```
useradd ${USER} dialout
```

Logout and login again.


3. Download the repos with the kobuki driver and utils

```
cd ~/ros2_ws/src
vcs import . < Turtlebot2/kobuki/third_parties.repos
```

4. Try to install from packages as much dependencies as possible

```
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
```

5. Compile the workspace

```
cd ~/ros2_ws
colcon build --symlink-install
```

6. Source the workspace or open a new terminal (if sources in .bashrc)
7. Use the kobuki utils to create the udev rules

```
cd src/ThirdParty/kobuki_ftdi
sudo mv 60-kobuki.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```

8. Let's launch the kobuki driver to test that everything went ok

On terminal 1:
```
ros2 launch ir_kobuki kobuki_rplidar.launch.py
```

You should have listened a sound that indicates that the driver succesfully communicated with the robot. Check permissions otherwise

On terminal 2:
```
ros2 topic list
```
You should be seeing the topics

## Setup RPLidar A2

The drivers have been already downloaded and built in the previous sections, but we need to manually create the udev rules

1. Create the file `/dev/udev.d/rplidar.xxx` with this content
2. restart udev 

```
sudo udevadm control --reload-rules && sudo udevadm trigger
```

4. Run the driver

```
ros2 launch rplidar_ros rplidar.launch.py
```

5. Visualize the `/scan` topic in RViz2 (frame `laser`)

## Launch everything

```
ros2 launch ir_kobuki kobuki_rplidar.launch.py
```

Open RViz2 and check TFs and Laser

# Launch kobuki simulated

## Pre-configuration

Move model to GAZEBO_MODEL_PATH
```
mkdir -p ~/.gazebo/models/ir_kobuki
cd <your-workspace>/src/Robots/kobuki/
cp -r models/ ~/.gazebo/models/ir_kobuki/models/meshes
```

## Launch Gazebo & Kobuki
```
ros2 launch ir_kobuki sim.launch.py
```


# openni2_camera


ROS2 wrapper for openni 2.0

Note: openni2_camera supports xtion devices, but not Kinects.

## Running ROS2 Driver

An example launch exists that loads just the camera component:

```
ros2 launch openni2_camera camera_only.launch.py
```

If you want to get a PointCloud2, use:

```
ros2 launch openni2_camera camera_with_cloud.launch.py
```
