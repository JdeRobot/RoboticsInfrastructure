# Setup Kobuki base

1. Download Kobuki_base repositories with drivers and utils inside your workspace (inside src directory):
~~~
vcs import < /kobuki_instructions/repos
~~~

2. Ensure you have all dependencies:
~~~
cd <workspace_root> && rosdep install --from-paths src --ignore-src -r -y
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
## Try Kobuki
Connect serial cable to the Robot and **Switch Kobuki ON**.
 
Kobuki’s default means of communication is over usb (it can instead use the serial comm port directly, more on that later). On most linux systems, your Kobuki will appear on /dev/ttyUSBO as soon as you connect the cable. This is a typical serial2usb device port and if you happen to be using more than one such device, Kobuki may appear at ttyUSB1, ttyUSB1, …
~~~
ls /dev/ttyUSB0
~~~ 
In order to provide a constant identifier for the connection, use the udev rule prepared in kobuki_ftdi:
~~~
sudo cp <workspace_root>/src/kobuki_ftdi/60-kobuki.rules /etc/udev/rules.d
sudo service udev reload
sudo service udev restart
~~~
Check for existance of `/dev/kobuki`
~~~
ls /dev/kobuki
~~~

Does kobuki appear as USB device?
~~~
lsusb
0403:6001 Future Technology Devices International, Ltd FT232 USB-Serial (UART) IC
~~~
Do you see it in dmesg when you insert the usb cable?
~~~
dmesg
    [  118.984126] usb 3-1: new full-speed USB device number 5 using xhci_hcd
    [  119.139253] usb 3-1: New USB device found, idVendor=0403, idProduct=6001
    [  119.139257] usb 3-1: New USB device strings: Mfr=1, Product=2, SerialNumber=3
    [  119.139259] usb 3-1: Product: iClebo Kobuki
    [  119.139261] usb 3-1: Manufacturer: Yujin Robot
    [  119.139263] usb 3-1: SerialNumber: kobuki_A505QO28
    [  119.150240] usbcore: registered new interface driver usbserial_generic
    [  119.150249] usbserial: USB Serial support registered for generic
    [  119.152383] usbcore: registered new interface driver ftdi_sio
    [  119.152403] usbserial: USB Serial support registered for FTDI USB Serial Device
    [  119.152505] ftdi_sio 3-1:1.0: FTDI USB Serial Device converter detected
    [  119.152530] usb 3-1: Detected FT232RL
    [  119.152665] usb 3-1: FTDI USB Serial Device converter now attached to ttyUSB0
~~~
and when you remove it?
~~~
dmesg
    [  184.386124] usb 3-1: USB disconnect, device number 5
    [  184.386507] ftdi_sio ttyUSB0: FTDI USB Serial Device converter now disconnected from ttyUSB0
    [  184.386547] ftdi_sio 3-1:1.0: device disconnected
~~~

Get the serial number:

~~~
sudo <workspace>/install/kobuki_ftdi/lib/kobuki_ftdi/get_serial_number
    1 device(s) found.

    Device #0
      Manufacturer : Yujin Robot
      Product      : iClebo Kobuki
      Serial Number: kobuki_A505QO28
~~~


Finally try to move Kobuki robot:
1. Launch Kobuki_node with specific configuration ( provided inside kobuki_launch package):
~~~
ros2 launch kobuki_launch kobuki_base.launch.py
# check that ros topics appear:
ros2 topic list
# teleoperate robot:
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args --remap /cmd_vel:=/commands/velocity
~~~

*Change topic names if necessary inside kobuki_ros/kobuki_node/src/kobuki_ros.cpp* 