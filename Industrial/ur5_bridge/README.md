# ur5_bridge

Makes a real UR5 (CB3) or UR5e (e-Series) look like the simulated UR5, so
MoveIt, the ros2srrc nodes and the pick_place HAL run unchanged. The same
exercise code moves the simulated and the real robot.

The arm runs on the official `ur_robot_driver`, already in the RADI image.
This package adds what the driver does not cover:

- `gripper_node`, drives the Robotiq 2F-85 and serves it as the simulated
  `gripper_controller`.
- `status_node`, explains in the log why the arm does not move and recovers
  it after a stop.

Launched through `CustomRobots/robot_arms/launch/ur5_physical.launch.py`, the
launch file used for scenes of type physical. It uses the official UR
description for the chosen model, not the vendored one of the simulation.

## Quick start

1. Plug this computer into the robot with a cable and give it a fixed
   address on the robot network, for example `192.168.0.50/24` for a robot
   at `192.168.0.4`. `ping` the robot to check it.
2. On the pendant power the robot on and press START to release the brakes.
   On a UR5e switch it to Remote Control with the icon at the top right
   corner, outside the Initialize or Settings screens. The first time enable
   it in Settings > System > Remote Control. Both robots need the Robotiq
   URCap installed for the gripper, as it usually is.
3. Start the RoboticsAcademy docker with the robot settings and the ports the
   robot connects back to:

```
docker run ... \
  -e UR_TYPE=ur5e -e UR_ROBOT_IP=192.168.1.102 -e UR_REVERSE_IP=192.168.1.10 \
  -p 50001-50004:50001-50004 \
  jderobot/robotics-academy
```

`UR_REVERSE_IP` is this computer's address on the robot network.

4. Open pick_place and choose the Ur5 Physical world.

## Environment variables

| Variable | Default | Meaning |
| --- | --- | --- |
| `UR_TYPE` | `ur5e` | `ur5` for CB3, `ur5e` for e-Series |
| `UR_ROBOT_IP` | `192.168.56.101` | Robot address |
| `UR_REVERSE_IP` | empty | Address the robot connects back to, empty lets the driver guess it, which only works with `--network host` |
| `UR_HEADLESS` | `true` | `true` sends the control program from here. `false` needs a program with the External Control URCap running on the pendant |
| `UR_GRIPPER` | `auto` | `urcap`, `rtu`, `none`, or `auto` that tries the URCap first and then a Modbus RTU serial port |
| `UR_TOOL_COMMUNICATION` | `false` | e-Series only, `true` exposes the wrist RS485 as `/tmp/ttyUR` for a gripper without URCap |
| `UR_KINEMATICS` | empty | Calibration yaml from `ur_calibration`, empty uses the factory kinematics |

The same names in lowercase are launch arguments that override them.

In Remote Control the pendant locks its speed slider, set it from the docker:

```
ros2 service call /io_and_status_controller/set_speed_slider \
  ur_msgs/srv/SetSpeedSliderFraction '{speed_slider_fraction: 0.5}'
```

## Safety

- MoveIt does not know about the table or anything around the robot, there
  is no collision model.
- The pick_place coordinates of the simulation belong to another table, do
  not run a simulation solution on the real robot.
- Prefer absolute targets above a minimum height over chains of relative
  moves, a failed step in a chain can end up against the table.
- Start with the speed slider low and keep a hand near the emergency stop.

## Interfaces

| Simulated arm | Real arm |
| --- | --- |
| `joint_trajectory_controller` of `gz_ros2_control` | Same name, a `ScaledJointTrajectoryController` of the UR driver. It follows the pendant speed slider and pauses on stops |
| `gripper_controller` | `gripper_node`, the joint position 0 to 0.80285 maps to the Robotiq position 0 to 255 |
| `/joint_states` | Arm from the driver, gripper from `gripper_node` |
| `/gripper_auto_attach` | Not used, the real fingers hold the object |

A gripper that stops on an object before the target counts as a successful
grasp.

## Gripper connection

- `urcap`, the Robotiq URCap socket on the robot, port 63352. Works on CB3
  and e-Series, the gripper can be wired to the wrist or to the control box.
- `rtu`, Modbus RTU at 115200 baud. Either the e-Series wrist through
  `UR_TOOL_COMMUNICATION=true`, or a Robotiq USB adapter plugged into this
  computer, passed to the docker as in `dobot_magician_bridge`.

## Stops

After a power off, a protective stop, an emergency stop or any other safety
stop, `status_node` aborts the running trajectory, so the arm never resumes
an old move by itself. When the robot is ready again it sends the control
program again in headless mode and the next command works. With
`UR_HEADLESS=false` press play on the pendant.

A lost network connection also aborts the move, the robot stops by itself
when it stops hearing from this computer. Once the network is back the
program is sent again. For a few seconds after that the driver can drop the
connection again, each drop is recovered within a second or two but a move
running at that moment fails.

After an emergency stop the Robotiq gripper comes back deactivated,
`gripper_node` activates it again on the next command, so the fingers open
and close once.

## Calibration

Every UR has small factory differences from the nominal kinematics. For
accurate picks extract them once per robot:

```
ros2 launch ur_calibration calibration_correction.launch.py \
  robot_ip:=<robot ip> target_filename:=/path/ur5e_calibration.yaml
```

and set `UR_KINEMATICS` to that file.

## Possible errors

| Log message | Fix |
| --- | --- |
| `Failed to connect to robot on IP ...` | Wrong `UR_ROBOT_IP` or robot not reachable, the driver keeps retrying |
| `robot in Local mode, switch it to Remote Control on the pendant` | Switch it to Remote Control, the program is sent as soon as it is |
| `the robot did not start the control program sent from here` | UR5e not in Remote Control, or the robot cannot reach this computer, check `UR_REVERSE_IP` and the published ports |
| Error `C210A0` on the pendant | The robot is in Local mode, switch it to Remote Control |
| Remote Control icon greyed out | Leave the Initialize or Settings screen first |
| `robot powered on with the brakes locked` | Release the brakes on the pendant |
| `robot stopped, protective stop` | Unlock it on the pendant |
| `Robotiq gripper not found` | Robotiq URCap not installed or gripper not powered, or set `UR_GRIPPER` |
| `The connected robot is of type ... but the driver was configured for type ...` | `UR_TYPE` does not match the robot, the driver refuses to start so it never moves with the wrong kinematics |
| `The calibration parameters of the connected robot don't match` | Expected without `UR_KINEMATICS`, see Calibration |

## Tested

On a real UR5e (PolyScope 5.12.6, reduced safety mode, no gripper): pick_place
HAL joint and Cartesian moves and a repeated pick and place sequence.

Against the official URSim for e-Series (UR5e, PolyScope 5.26) and CB3 (UR5,
PolyScope 3.15) with a simulated Robotiq: pick_place HAL moves and gripper,
both gripper connections, docker behind NAT, power loss and network loss in
the middle of a move, gripper deactivation and launching with the robot
powered off. URSim cannot press an emergency stop or trigger a protective
stop, those use the same recovery as the power loss but were not run. The non
headless mode with the External Control URCap and the gripper on a real robot
were not tested.
