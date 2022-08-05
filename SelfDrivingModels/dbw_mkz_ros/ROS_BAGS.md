# Setup
This tutorial assumes your workspace is already setup. If not, follow this [tutorial](ROS_SETUP.md) first.

# Download
Download one or more bag file recordings

* ~11MB [mkz_20151207](https://bitbucket.org/DataspeedInc/dbw_mkz_ros/downloads/mkz_20151207.bag)
* ~254MB [mkz_20151207_extra](https://bitbucket.org/DataspeedInc/dbw_mkz_ros/downloads/mkz_20151207_extra.bag.tar.gz) (Includes Velodyne LIDAR and Oxford GPS)

# Playback
In separate tabs, run the following:

* Translate the CAN messages: ```roslaunch dbw_mkz_can offline.launch```
* Visualize with RViz: ```roslaunch dbw_mkz_description rviz.launch```
* Playback the recording: ```rosbag play mkz_20151207.bag --clock```

If using one of the recordings with 'extra' run the following to provide a tf reference for the Velodyne LIDAR:

* ```rosrun tf static_transform_publisher 0.94 0 1.5 0.07 -0.02 0 base_footprint velodyne 50```
