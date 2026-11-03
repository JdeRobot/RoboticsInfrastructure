# TurtleBot3

Simulated Waffle and Burger, plus the physical Burger drivers.

## Physical Burger

The RoboticsBackend runs inside the Burger Raspberry Pi with the drivers, and the browser on your laptop connects to it. The robot publishes the same topics as the simulated Burger, so exercises need no changes. Available world: **Laser Mapping TurtleBot3 Burger Physical** in Laser Mapping.

### Requirements

- Raspberry Pi with a 64 bit OS (`uname -m` prints `aarch64`) and Docker.
- OpenCR flashed with the ROBOTIS ROS 2 firmware for the Burger.
- OpenCR on `/dev/ttyACM0` and lidar on `/dev/ttyUSB0`.

### Raspberry Pi setup (once)

Stop ModemManager from grabbing the OpenCR and give access to both ports:

```bash
sudo tee /etc/udev/rules.d/99-turtlebot3-cdc.rules > /dev/null <<'EOF'
ATTRS{idVendor}=="0483" ATTRS{idProduct}=="5740", ENV{ID_MM_DEVICE_IGNORE}="1", MODE:="0666"
ATTRS{idVendor}=="10c4" ATTRS{idProduct}=="ea60", ENV{ID_MM_DEVICE_IGNORE}="1", MODE:="0666"
EOF
sudo udevadm control --reload-rules && sudo udevadm trigger
```

### Run it on the Raspberry Pi

Use your usual compose file and add the two devices to the `robotics-academy` service:

```yaml
    devices:
      - /dev/ttyACM0:/dev/ttyACM0
      - /dev/ttyUSB0:/dev/ttyUSB0
```

For an LDS-02 lidar also add `environment: [LDS_MODEL=LDS-02]`. The default is LDS-01.

### Connect from your laptop

The frontend talks to `127.0.0.1`, so forward the two backend ports:

```bash
ssh -L 7163:localhost:7163 -L 7164:localhost:7164 <user>@<raspberry ip>
```

Open http://localhost:7164, go to Laser Mapping and choose **Laser Mapping TurtleBot3 Burger Physical**.

### Possible errors

| Symptom | Cause |
|---|---|
| `Failed to open the port` in the turtlebot3_node log | `/dev/ttyACM0` not passed to the container or the udev rule is missing |
| Laser data always empty | Wrong `LDS_MODEL` or `/dev/ttyUSB0` not passed to the container |
| The robot does not move | OpenCR firmware is not the ROS 2 Burger one |
