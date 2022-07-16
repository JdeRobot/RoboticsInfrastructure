# One Line SDK Update

* Use this option if the SDK has already been installed.
* Paste the following into a terminal to update the SDK. This script will update binaries and source code as necessary.
* ```bash <(wget -q -O - https://bitbucket.org/DataspeedInc/dbw_mkz_ros/raw/default/dbw_mkz/scripts/sdk_update.bash)```

# One Line SDK Install (binary)

* Use this option to install the SDK on a workstation that already has ROS installed.
* Paste the following into a terminal to install the SDK. This script will configure apt-get to connect to the Dataspeed server and install the SDK.
* ```bash <(wget -q -O - https://bitbucket.org/DataspeedInc/dbw_mkz_ros/raw/default/dbw_mkz/scripts/sdk_install.bash)```

# One Line ROS and SDK Install (binary)

* Use this option to install ROS and this SDK on a clean Ubuntu install.
* This should ONLY be run on a fresh install of [Ubuntu 14.04.5 Desktop](http://releases.ubuntu.com/14.04/ubuntu-14.04.5-desktop-amd64.iso) or [Ubuntu 16.04.x Desktop](http://releases.ubuntu.com/16.04/ubuntu-16.04.1-desktop-amd64.iso).
* Paste the following into a terminal to install ROS and this SDK. This script will change some operating system parameters, install ROS [Indigo](http://wiki.ros.org/indigo/Installation/Ubuntu) or [Kinetic](http://wiki.ros.org/kinetic/Installation/Ubuntu), install the SDK, and configure the joystick demo with rviz to run at startup.
* ```bash <(wget -q -O - https://bitbucket.org/DataspeedInc/dbw_mkz_ros/raw/default/dbw_mkz/scripts/ros_install.bash)```

# Manual install/update (source)

* Setup workspace
    * ```sudo apt-get install python-wstool```
    * ```mkdir -p ~/dbw_ws/src && cd ~/dbw_ws && wstool init src```
    * ```wstool merge -t src https://bitbucket.org/DataspeedInc/dbw_mkz_ros/raw/default/dbw_mkz.rosinstall```
* Update workspace and resolve dependencies
    * ```wstool update -t src```
    * ```rosdep update && rosdep install --from-paths src --ignore-src```
* Install udev rules
    * ```sudo cp ~/dbw_ws/src/dataspeed_can/dataspeed_can_usb/90-DataspeedUsbCanToolRules.rules /etc/udev/rules.d/```
    * ```sudo udevadm control --reload-rules && sudo service udev restart && sudo udevadm trigger```
* Build workspace
    * ```catkin_make -DCMAKE_BUILD_TYPE=Release```
* Source the workspace
    * ```source ~/dbw_ws/devel/setup.bash```

# Launch joystick demo
```bash
roslaunch dbw_mkz_joystick_demo joystick_demo.launch sys:=true
```

# Launch Drive-By-Wire system only
```bash
roslaunch dbw_mkz_can dbw.launch
```

# Launch RViz visualization
```bash
roslaunch dbw_mkz_description rviz.launch
```
