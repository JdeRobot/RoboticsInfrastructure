# MiR100 mock

Fake MiR100 to develop the real robot integration without hardware.

The real MiR runs its own ROS1 and exposes it through rosbridge (websocket, port 9090).
`mir_driver` (DFKI-NI/mir_robot, ROS1 Noetic) connects there and republishes the robot topics on the user's roscore.
This mock reproduces the robot side, so the driver runs unmodified.

- `mir_robot`: ROS1 master, rosbridge on 9090 and `fake_mir.py` (odom, f_scan, b_scan, scan, imu_data, tf, robot_state, cmd_vel as TwistStamped).
- `mir_driver`: the original `mir.launch` from source, host network, so its ROS1 master is on the host like a real setup.

```
docker compose up -d
docker exec -it mir_driver bash -lc 'source /ros_entrypoint.sh; rostopic list'
```

## Using it with the bridge

The bridge in `Industrial/mir100_bridge` talks straight to the robot by default,
so for the physical world only the fake robot is needed:

```
docker compose up --build mir_robot
```

The bridge runs inside the RADI container, so tell it where the fake robot is,
for example with `MIR100_ROBOT_IP` set to the address of your machine.

To try the `driver` mode instead, start both services and launch the physical
world with `mode:=driver`.

To use the real robot, skip this mock and connect to the robot's network.
