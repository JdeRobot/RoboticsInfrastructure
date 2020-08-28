source /opt/ros/foxy/setup.bash
#source /opt/overlay_ws/install/setup.sh && cd /opt/warehouse_ws/ && colcon build --symlink-install
source /opt/warehouse_ws/install/setup.sh

sleep 2s

#ros2 launch slam_toolbox online_async_launch.py &
#
#sleep 2s


#ros2 launch amazon_robot_bringup  amazon_warehouse_world.py #slam:=True

#ros2 launch amazon_robot_bringup  amazon_robot_in_tb3_world.py


ros2 launch amazon_robot_bringup  amazon_robot_in_aws_world.py

#sleep 20s
#
#cd /opt/warehouse_ws/exercise && python3 single_robot.py &