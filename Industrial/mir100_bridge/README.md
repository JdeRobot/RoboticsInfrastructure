# mir100_bridge

ROS2 node that republishes a MiR100 (real or mocked, see `CustomRobots/mir100/mir100_mock`) as the
same topics the simulated MiR100 uses, so the HAL does not see any difference
between sim and real robot.

It never installs ROS1. It connects to the student's ROS1 side as a plain
rosbridge websocket client, the same technique `mir_driver` itself uses to
reach the robot, just one layer up. That means the whole node is pure
ROS2/rclpy and can run inside the RoboticsAcademy docker like any other
exercise node.

Launched through `CustomRobots/mir100/launch/mir100_physical.launch.py`, the launch file used
for scenes of type physical.

## Topics

| ROS1 (mir_driver) | ROS2 (this node) |
| --- | --- |
| `/cmd_vel` | `/mir100/cmd_vel` |
| `/odom` | `/mir100/odom` |
| `/f_scan` | `/mir100/front_laser/scan` |
| `/b_scan` | `/mir100/back_laser/scan` |
| `/imu_data` | `/mir100/imu` |

## Parameters

- `ros1_hostname`, the machine running rosbridge_server on top of the
  student's ROS1 master, defaults to `localhost`.
- `ros1_port`, defaults to `9091`.
- `namespace`, defaults to `mir100`.

## Dependency

Needs `roslibpy`, a plain Python websocket client, not a ROS package. RADI
installs it in `scripts/RADI/Dockerfile.dependencies_humble`. Outside RADI
use `pip install roslibpy`.
