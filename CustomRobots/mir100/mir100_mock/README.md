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

To use the real robot, skip `mir_robot` and set `mir_hostname` to the robot IP.
