# mir100_bridge

ROS2 node that republishes a MiR100 (real or mocked, see `CustomRobots/mir100/mir100_mock`) as the
same topics the simulated MiR100 uses, so the HAL does not see any difference
between sim and real robot.

It never installs ROS1. It connects as a plain rosbridge websocket client, so
the whole node is pure ROS2/rclpy and runs inside the RoboticsAcademy docker
like any other exercise node.

Launched through `CustomRobots/mir100/launch/mir100_physical.launch.py`, the launch file used
for scenes of type physical.

## Modes

- `robot` (default): talks straight to the MiR100, which already exposes
  rosbridge on port 9090. Nothing to launch besides the exercise, the robot
  only has to be reachable on the network. Its address defaults to
  `192.168.12.20`, the one it has on its own wifi.
- `driver`: talks to a `mir_driver` running outside the docker, with its own
  `rosbridge_server` on port 9091. For setups that already have their own
  driver.

## Topics

| MiR100 or mir_driver | ROS2 (this node) |
| --- | --- |
| `/cmd_vel` | `/mir100/cmd_vel` |
| `/odom` | `/mir100/odom` |
| `/f_scan` | `/mir100/front_laser/scan` |
| `/b_scan` | `/mir100/back_laser/scan` |
| `/imu_data` | `/mir100/imu` |

In `robot` mode the twist is sent with a header, as the MiR software 2.7 and
newer expects, `mir_driver` does that itself in `driver` mode.

## Parameters

- `mode`, `robot` or `driver`, defaults to `robot`.
- `ros1_hostname`, where to connect. In `robot` mode it defaults to the
  `MIR100_ROBOT_IP` environment variable, then `192.168.12.20`. In `driver`
  mode it is the machine running `mir_driver`, resolved when empty from the
  `MIR100_ROS1_HOST` environment variable, then `host.docker.internal`, then
  the container's default gateway (the docker host on Linux), and finally
  `localhost`.
- `ros1_port`, defaults to `9090` in `robot` mode and `9091` in `driver` mode.
- `namespace`, defaults to `mir100`.

## Dependency

Needs `roslibpy`, a plain Python websocket client, not a ROS package. RADI
installs it in `scripts/RADI/Dockerfile.dependencies_humble`. Outside RADI
use `pip install roslibpy`.
