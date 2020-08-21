source /opt/ros/foxy/setup.bash
#source /opt/overlay_ws/install/setup.sh && cd /opt/warehouse_ws/ && colcon build --symlink-install
source /opt/warehouse_ws/install/setup.sh

sleep 2s

ros2 launch amazon_robot_bringup  amazon_warehouse_world.py