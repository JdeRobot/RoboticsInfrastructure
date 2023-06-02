 # Setup RpLidar

1. Allow access to serial port; you can do it 2 ways:
    
    - 1.1 allow full and direct access to serial ports adding your user to `dialout` group:
        ~~~
        # check your user
        id
        # add your user to dialout if is not already done
        sudo adduser <user> dialout 
        # restart
        reboot
        ~~~
    - 1.2 give read and write permissions to the serial specific port:
        ~~~
        chmod 777 /dev/ttyUSB0
        ~~~

2. Download RpLidar repository with drivers and utils inside your workspace (inside src directory):
~~~
vcs import < rplidar_instructions/repos
~~~

3. Build workspace:
~~~
cd <workspace_root> && colcon_build --symlink-install
~~~

4. Source workspace:
~~~
source <workspace_root>/install/setup.bash
~~~
#
## Try RpLidar

5. Create udev rules executing rplidar_ros package's script:
~~~
./<path_to_rplidar_ros_pkg>/scripts/create_udev_rules.sh
~~~
6. Connect RpLidar to Serial port; check that its turning (is ON). Try RpLidar with RViz:
~~~
ros2 launch rplidar_ros view_rplidar.launch.py
~~~

*Rplidar node's name is: rplidar_composition*
