# dobot_magician_bridge

ROS2 driver for the real Dobot Magician. It talks to the robot's firmware over
its USB serial port and exposes the same interfaces as the simulated arm, so
MoveIt, the ros2srrc nodes and the HAL run unchanged. The same exercise code
moves the simulated and the real robot.

The Dobot has no ROS inside, only a proprietary firmware that speaks the Dobot
Communication Protocol. This node is the driver itself, pure rclpy with no
extra dependencies, and runs inside the RoboticsAcademy docker like any other
exercise node.

Launched through `CustomRobots/robot_arms/launch/dobot_magician_physical.launch.py`,
the launch file used for scenes of type physical.

## Interfaces

| Simulated arm | Real arm (this node) |
| --- | --- |
| `gz_ros2_control` joint trajectory controller | `/joint_trajectory_controller/follow_joint_trajectory`, each trajectory becomes firmware point to point moves timed to the planned duration |
| `joint_state_broadcaster` | `/joint_states` read from the robot's encoders |
| `gz_link_attacher` on `/gripper_auto_attach` | `/gripper_auto_attach` turns the suction cup pump on and off |

The firmware measures J3 from the table, the URDF from the rear arm, so
`joint_3 = J3 - J2`. The parallelogram mimic joints are published too.

## Homing

Straight after power on the arm rests folded low, and the firmware homing
sweeps the base from there, dragging the tool over the table. The node raises
J2 and J3 first, base untouched, then homes. It homes once per robot power on,
RAM relaunches the robot every time the exercise code is stopped and that
does not home again.

## Parameters

- `port`, `auto` finds the Dobot by its USB ids (CP2102 or CH340), or a device
  path like `/dev/ttyUSB0`.
- `end_effector`, defaults to `suction_cup`.
- `homing`, `auto` (default) homes once per power on, `always` or `never`.
- `rate`, joint_states rate in Hz, defaults to `20`.

## USB access from the docker

The container needs the robot's serial port. Plugging it before or after
starting the container both work with:

```
-v /dev:/host_dev:ro --device-cgroup-rule='c 188:* rmw' --device-cgroup-rule='c 166:* rmw'
```

The host `/dev` goes to `/host_dev` instead of `/dev`, so the host terminals
in `/dev/pts` never show up inside the container. Already set in
`compose_cfg/dev_humble_*.yaml` of RoboticsAcademy. Only works on Linux hosts,
Docker Desktop on Windows and macOS does not pass USB devices through.

## Not using pyserial

The RADI image ships an unrelated PyPI package also called `serial` that
shadows pyserial, so the port is opened with plain `termios`.
