# Robots, scenes and worlds in RI

Status: `ok` merged and working, `wip` in an open branch, `todo` pending.

Previews live in `Docs/media/robots/` and `Docs/media/scenes/` (960x540 JPG). Longer videos go on YouTube and the cell links to them with a GIF as thumbnail.

## Simulated robots

Launch paths are relative to `CustomRobots/`. Every noise/sensor variant is a row in the `robots` table of `database/worlds.sql`, here they are grouped by physical platform.

### Mobile robots

| Robot              | Status | Media&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Launch file                                                | Entity                   | Configs                                | Sensors                         | Actuators                       | Notes                              |
| ------------------ | :----: | :---: | ---------------------------------------------------------- | ------------------------ | -------------------------------------- | ------------------------------- | ------------------------------- | ---------------------------------- |
| F1 car             |   ok   | <img src="media/robots/f1.jpg" width="160"> | f1/launch/f1.launch.py                                     | f1                       | mode=(holo/ackermann) sensor=(camera/laser) | camera or laser            | ackermann or holonomic steering |                                    |
| Autonomous car     |   ok   | <img src="media/robots/autonomous_car.jpg" width="160"> | autonomous_car/launch/autonomous_car.launch.py             | autonomous_car           | mode=(holonomic/ackermann) sensor=(camera/laser/lidar) | camera, lidar or 3 lasers | ackermann or holonomic steering |                       |
| Vacuum cleaner     |   ok   | <img src="media/robots/vacuum_cleaner.jpg" width="160"> | vacuum_cleaner/launch/vacuum_cleaner.launch.py             | vacuum_cleaner           | sensor=(camera/laser)                  | camera or laser                 | differential drive              | Broken bumper in URDF              |
| TurtleBot 2        |   ok   | <img src="media/robots/turtlebot2.jpg" width="160"> | Turtlebot2/launch/turtlebot2.launch.py                     | turtlebot2               | sensor=(camera/stereo)                 | camera or stereo, laser, IMU    | differential drive              |                                    |
| TurtleBot 3 Waffle |   ok   | <img src="media/robots/turtlebot3_waffle.jpg" width="160"> | turtlebot3/launch/turtlebot3.launch.py                     | turtlebot3               | noise=(none/low/med/high) marker       | camera or laser, IMU            | differential drive              |                                    |
| TurtleBot 3 Burger |   ok   | <img src="media/robots/turtlebot3_burger.jpg" width="160"> | turtlebot3/launch/turtlebot3_burger.launch.py              | turtlebot3               | noise=(none/low/med/high) sensor=(laser/camera) | laser, IMU, camera (optional) | differential drive    |                                    |
| Rover 4wd          |   ok   | <img src="media/robots/rover_4wd.jpg" width="160"> | rover_4wd/launch/rover_4wd.launch.py                       | rover_4wd                | noise=(none/low/high)                  | laser, IMU                      | differential drive              |                                    |
| Dingo              |   ok   | <img src="media/robots/dingo.jpg" width="160"> | dingo/launch/dingo.launch.py                               | do150                    | noise=(none/low/med/high)              | laser, IMU                      | mecanum drive                   |                                    |
| MiR100             |   ok   | <img src="media/robots/mir100.jpg" width="160"> | mir100/launch/mir100.launch.py                             | mir100                   | noise=(none/low/med/high)              | 2x laser, IMU                   | differential drive              |                                    |
| Logistic Holonomic |   ok   | <img src="media/robots/logistic_holonomic.jpg" width="160"> | logistic_holonomic_robot/launch/logistic_holonomic_robot.launch.py | logistic_holonomic_robot |                                | none                            | holonomic drive                 | Ball joint fails in URDF           |
| Logistic Ackermann |   ok   | <img src="media/robots/logistic_ackermann.jpg" width="160"> | logistic_ackermann_robot/launch/logistic_ackermann_robot.launch.py | logistic_ackermann_robot |                                | none                            | ackermann steering              |                                    |

### Drones

| Robot     | Status | Media&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Launch file                          | Entity                | Configs                                  | Sensors                     | Actuators                                        | Notes |
| --------- | :----: | :---: | ------------------------------------ | --------------------- | ---------------------------------------- | --------------------------- | ------------------------------------------------ | ----- |
| Quadrotor |   ok   | <img src="media/robots/quadrotor.jpg" width="160"> | quadrotor/launch/quadrotor.launch.py | drone / drone_mouse   | sensor=(camera) color gripper=(true/false) | frontal and ventral camera, IMU | multirotor (4 motors), optional magnetic gripper |       |

### Robot arms

| Robot          | Status | Media&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Launch file                                   | Entity                 | Configs         | Sensors                | Actuators                          | Notes                    |
| -------------- | :----: | :---: | --------------------------------------------- | ---------------------- | --------------- | ---------------------- | ---------------------------------- | ------------------------ |
| UR5            |   ok   | <img src="media/robots/ur5.jpg" width="160"> | robot_arms/launch/ur5.launch.py               | ur5_robotiq            | sensor=(camera) | camera (optional)      | 6-DOF arm + Robotiq 2F-85 gripper  | Broken Reset             |
| UR3            |   ok   | <img src="media/robots/ur3.jpg" width="160"> | robot_arms/launch/ur3.launch.py               | ur3_robotiq            | sensor=(camera) | camera (optional)      | 6-DOF arm + Robotiq 2F-85 gripper  |                          |
| UR10 Suction   |   ok   | <img src="media/robots/ur10_suction.jpg" width="160"> | robot_arms/launch/ur10_suction.launch.py      | ur10_suction           |                 | suction contact sensor | 6-DOF arm + suction gripper        |                          |
| Dobot Magician |  wip   | <img src="media/robots/dobot_magician.jpg" width="160"> | robot_arms/launch/dobot_magician.launch.py    | dobot_magician_gripper |                 | none                   | 4-DOF arm + parallel gripper       | Branch `dobot-magician`  |

### Mobile manipulators

| Robot         | Status | Media&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Launch file                                  | Entity        | Configs | Sensors                         | Actuators                                        | Notes                            |
| ------------- | :----: | :---: | -------------------------------------------- | ------------- | ------- | ------------------------------- | ------------------------------------------------ | -------------------------------- |
| XLeRobot      |   ok   | <img src="media/robots/xlerobot.jpg" width="160"> | xlerobot/launch/xlerobot.launch.py           | xlerobot      |         | RGB-D head camera, 2x wrist camera | 3-wheel omni base + 2x 5-DOF arm with gripper | MoveIt2                          |
| MMO-500       |   ok   | <img src="media/robots/mmo500.jpg" width="160"> | mmo500/launch/mmo500.launch.py               | mmo500        |         | 2x laser                        | mecanum base + UR10 + Robotiq 2F-85              | MoveIt2                          |
| myAGV mechArm |  wip   | <img src="media/robots/myagv_mecharm.jpg" width="160"> | myagv_mecharm/launch/myagv_mecharm.launch.py | myagv_mecharm |         | laser, camera                   | mecanum base + 6-DOF mechArm 270 + adaptive gripper | Branch `mobile-manipulation-agv` |

## Physical robots

The scene is of type `physical`, no simulator runs. The robot launch file brings the real robot topics into ROS2 with the same names as its simulated twin, so the same HAL works on both.

| Robot       | Status | Media | Simulated twin | Launch file                              | Connection                               | Notes                                                    |
| ----------- | :----: | :---: | -------------- | ---------------------------------------- | ---------------------------------------- | -------------------------------------------------------- |
| MiR100      |  wip   |       | MiR100         | mir100/launch/mir100_physical.launch.py  | rosbridge websocket to the MiR (ROS1)    | Bridge merged (#810), first real robot test with partner |
| TurtleBot 2 |  todo  |       | TurtleBot 2    |                                          | USB (Kobuki base + RPLidar)              | `Turtlebot2/Turtlebot2_physical` not wired to RAM        |
| Tello       |  todo  |       | Quadrotor      |                                          | WiFi                                     | `tello_phy` driver not wired to RAM                      |
| UR arms     |  todo  |       | UR3 / UR5      |                                          | Ethernet (`ur_robot_driver`)             | Launchers hardcode simulation                            |

## Scenes

Launch files live in `/opt/jderobot/Launchers`. "Robots" lists the robots the database spawns in that scene.

### Circuits and roads

| Scene               | Status | Media | Launch file                   | Robots                    | Notes |
| ------------------- | :----: | :---: | ----------------------------- | ------------------------- | ----- |
| Simple Circuit      |   ok   | <img src="media/scenes/simple_circuit.jpg" width="160"> | simple_circuit.launch.py      | F1                        |       |
| Montmelo Circuit    |   ok   | <img src="media/scenes/montmelo_circuit.jpg" width="160"> | montmelo_circuit.launch.py    | F1                        |       |
| Montreal Circuit    |   ok   | <img src="media/scenes/montreal_circuit.jpg" width="160"> | montreal_circuit.launch.py    | F1                        |       |
| Nurburgring Circuit |   ok   | <img src="media/scenes/nurburgring_circuit.jpg" width="160"> | nurburgring_circuit.launch.py | F1                        |       |
| Monaco Circuit      |   ok   | <img src="media/scenes/monaco_circuit.jpg" width="160"> | monaco_circuit.launch.py      | F1                        |       |
| Spa Circuit         |   ok   | <img src="media/scenes/spa_circuit.jpg" width="160"> | spa_circuit.launch.py         | F1                        |       |
| Obstacle Avoidance  |   ok   | <img src="media/scenes/obstacle_avoidance.jpg" width="160"> | obstacle_avoidance_h.launch.py | F1 (laser)               |       |
| City Large          |   ok   | <img src="media/scenes/city_large.jpg" width="160"> | basic_city.launch.py          | Autonomous car            |       |
| Car Junction        |   ok   | <img src="media/scenes/car_junction.jpg" width="160"> | car_junction.launch.py        | Autonomous car            |       |
| Autopark_line       |   ok   | <img src="media/scenes/autopark_line.jpg" width="160"> | autopark_line.launch.py       | Autonomous car            |       |
| Autopark_battery    |   ok   | <img src="media/scenes/autopark_battery.jpg" width="160"> | autopark_battery.launch.py    | Autonomous car            |       |
| Autopark_sideways   |   ok   | <img src="media/scenes/autopark_sideways.jpg" width="160"> | autopark_sideways.launch.py   | Autonomous car            |       |
| Autoparking Gas Station: In battery  |  todo  |  | gas_station_battery_ackermann.launch.py | Autonomous car | Not in database |
| Autoparking Gas Station: In line     |  todo  |  | gas_station_line_ackermann.launch.py    | Autonomous car | Not in database |
| Autoparking Gas Station: Parking lot |  todo  |  | gas_station_parking_ackermann.launch.py | Autonomous car | Not in database |

### Houses and indoor

| Scene                 | Status | Media | Launch file                         | Robots                          | Notes                       |
| --------------------- | :----: | :---: | ----------------------------------- | ------------------------------- | --------------------------- |
| Small House           |   ok   | <img src="media/scenes/small_house.jpg" width="160"> | small_house.launch.py               | Vacuum cleaner, TurtleBot 3 Burger |                          |
| Small House Roof      |   ok   | <img src="media/scenes/small_house_roof.jpg" width="160"> | small_house_roof.launch.py          | Vacuum cleaner (camera)         |                             |
| Vacuums House Markers |   ok   | <img src="media/scenes/vacuums_house_markers.jpg" width="160"> | detailed_house.launch.py            | TurtleBot 3 Waffle, TurtleBot 3 Burger |                      |
| Vacuums Party House   |  wip   | <img src="media/scenes/vacuums_party_house.jpg" width="160"> | vacuum_party_house.launch.py        | Vacuum cleaner                  | Branch `vacuum-gamification` |
| XLeRobot Home         |   ok   | <img src="media/scenes/xlerobot_home.jpg" width="160"> | xlerobot_home.launch.py             | XLeRobot                        |                             |
| Follow Person         |   ok   | <img src="media/scenes/follow_person.jpg" width="160"> | follow_person_harmonic.launch.py    | TurtleBot 2                     |                             |
| Follow Person Teleop  |   ok   | <img src="media/scenes/follow_person_teleop.jpg" width="160"> | follow_person_teleop_harmonic.launch.py | TurtleBot 2                 |                             |
| 3d Reconstruction     |   ok   | <img src="media/scenes/3d_reconstruction.jpg" width="160"> | 3d_reconstruction.launch.py         | TurtleBot 2 (stereo)            |                             |
| UDC Grid World        |  wip   | <img src="media/scenes/udc_grid_world.jpg" width="160"> | udc_grid_fig3.launch.py             | TurtleBot 3 Burger              | Branch `lab-acoruna`        |
| UDC Lab Grid World    |  wip   | <img src="media/scenes/udc_lab_grid_world.jpg" width="160"> | udc_grid_fig3_lab.launch.py         | TurtleBot 3 Burger              | Branch `lab-acoruna`        |
| Restaurant            |  todo  |       | restaurant.launch.py                |                                 | Not in database        |

### Warehouses and logistics

| Scene                         | Status | Media | Launch file                             | Robots                                              | Notes                                |
| ----------------------------- | :----: | :---: | --------------------------------------- | --------------------------------------------------- | ------------------------------------ |
| Warehouse 1                   |   ok   | <img src="media/scenes/warehouse1.jpg" width="160"> | warehouse1.launch.py                    | Logistic Holonomic, Logistic Ackermann, MiR100, XLeRobot |                                 |
| Warehouse 2                   |   ok   | <img src="media/scenes/warehouse2.jpg" width="160"> | warehouse2.launch.py                    | Logistic Holonomic, Logistic Ackermann              |                                      |
| Laser Mapping Warehouse       |   ok   | <img src="media/scenes/laser_mapping_warehouse.jpg" width="160"> | laser_mapping.launch.py                 | Dingo                                               |                                      |
| Small Laser Mapping Warehouse |   ok   | <img src="media/scenes/small_laser_mapping_warehouse.jpg" width="160"> | small_laser_mapping.launch.py           | Dingo, TurtleBot 3 Burger                           |                                      |
| Rover 4wd Warehouse           |   ok   | <img src="media/scenes/rover_4wd_warehouse.jpg" width="160"> | rover_4wd_warehouse.launch.py           | Rover 4wd                                           |                                      |
| Mobile Manipulation Warehouse |   ok   | <img src="media/scenes/mobile_manipulation_warehouse.jpg" width="160"> | mobile_manipulation_warehouse.launch.py | MMO-500                                             |                                      |
| Warehouse Delivery            |  wip   | <img src="media/scenes/warehouse_delivery.jpg" width="160"> | warehouse_delivery.launch.py            | myAGV mechArm                                       | Branch `mobile-manipulation-agv`     |
| Mir100 Warehouse              |  todo  |       | mir100_warehouse.launch.py              | MiR100                                              | Branch `mir100-exercise`, on hold    |

### Drones

| Scene                  | Status | Media | Launch file                         | Robots                          | Notes |
| ---------------------- | :----: | :---: | ----------------------------------- | ------------------------------- | ----- |
| Rescue People          |   ok   | <img src="media/scenes/rescue_people.jpg" width="160"> | rescue_people.launch.py             | Quadrotor                       |       |
| Follow Road            |   ok   | <img src="media/scenes/follow_road.jpg" width="160"> | follow_road.launch.py               | Quadrotor                       |       |
| Drone Gymkhana         |   ok   | <img src="media/scenes/drone_gymkhana.jpg" width="160"> | drone_gymkhana.launch.py            | Quadrotor                       |       |
| Tower Inspection       |   ok   | <img src="media/scenes/tower_inspection.jpg" width="160"> | power_tower_inspection.launch.py    | Quadrotor                       |       |
| Labyrinth Escape       |   ok   | <img src="media/scenes/labyrinth_escape.jpg" width="160"> | labyrinth_escape.launch.py          | Quadrotor                       |       |
| Package delivery       |   ok   | <img src="media/scenes/package_delivery.jpg" width="160"> | package_delivery.launch.py          | Quadrotor (magnet)              |       |
| Drone Hangar           |   ok   | <img src="media/scenes/drone_hangar.jpg" width="160"> | drone_hangar.launch.py              | Quadrotor                       |       |
| Position Control       |   ok   | <img src="media/scenes/position_control.jpg" width="160"> | position_control.launch.py          | Quadrotor                       |       |
| Drone Cat Mouse Easy   |   ok   | <img src="media/scenes/drone_cat_mouse.jpg" width="160"> | drone_cat_mouse.launch.py           | 2x Quadrotor                    |       |
| Drone Cat Mouse Medium |   ok   | <img src="media/scenes/drone_cat_mouse.jpg" width="160"> | drone_cat_mouse_medium.launch.py    | 2x Quadrotor                    |       |
| Drone Cat Mouse Hard   |   ok   | <img src="media/scenes/drone_cat_mouse.jpg" width="160"> | drone_cat_mouse_hard.launch.py      | 2x Quadrotor                    |       |
| Visual Lander          |   ok   | <img src="media/scenes/visual_lander.jpg" width="160"> | visual_lander.launch.py             | Quadrotor                       |       |
| Visual Lander Circuit  |   ok   | <img src="media/scenes/visual_lander_circuit.jpg" width="160"> | visual_lander_circuit.launch.py     | Quadrotor                       |       |
| Follow Turtlebot       |   ok   | <img src="media/scenes/follow_turtlebot.jpg" width="160"> | follow_turtlebot.launch.py          | Quadrotor, TurtleBot 3 Waffle   |       |

### Industrial

| Scene                | Status | Media | Launch file                  | Robots          | Notes                  |
| -------------------- | :----: | :---: | ---------------------------- | --------------- | ---------------------- |
| Pick And Place       |   ok   | <img src="media/scenes/pick_place.jpg" width="160"> | pick_place.launch.py         | UR5             | Reset broken           |
| Machine Vision       |   ok   | <img src="media/scenes/machine_vision.jpg" width="160"> | machine_vision.launch.py     | UR5 (camera)    | Reset broken           |
| Conveyor             |   ok   | <img src="media/scenes/conveyor.jpg" width="160"> | sausage_exercise.launch.py   | UR3 (camera)    |                        |
| Palletizing          |   ok   | <img src="media/scenes/palletizing.jpg" width="160"> | palletizing.launch.py        | UR10 Suction    |                        |
| Dobot Pick And Place |  wip   | <img src="media/scenes/dobot_pick_place.jpg" width="160"> | dobot_pick_place.launch.py   | Dobot Magician  | Branch `dobot-exercise` |

### Physical

| Scene           | Status | Media | Launch file          | Robots           | Notes                    |
| --------------- | :----: | :---: | -------------------- | ---------------- | ------------------------ |
| Mir100 Physical |  wip   |       | physical.launch.py   | MiR100 (physical) | Empty scene, real robot |

## Showcase videos

Short commercial-style videos of the strongest robot and scene combinations.

| Video                          | Robots                       | Scene                         | Status | Link |
| ------------------------------ | ---------------------------- | ----------------------------- | :----: | ---- |
| Dual-arm home pick and place   | XLeRobot                     | XLeRobot Home                 |  todo  |      |
| Mobile manipulation with workers | myAGV mechArm              | Warehouse Delivery            |  todo  |      |
| Industrial mobile manipulator  | MMO-500                      | Mobile Manipulation Warehouse |  todo  |      |
| Sim to real logistics          | MiR100 + MiR100 (physical)   | Warehouse 1 + Mir100 Physical |  todo  |      |
| Drone chases ground robot      | Quadrotor + TurtleBot 3 Waffle | Follow Turtlebot            |  todo  |      |
| Drone cat and mouse            | 2x Quadrotor                 | Drone Cat Mouse Hard          |  todo  |      |
| Drone package delivery         | Quadrotor (magnet)           | Package delivery              |  todo  |      |
| F1 racing                      | F1                           | Monaco Circuit                |  todo  |      |
| Autonomous driving in the city | Autonomous car               | City Large                    |  todo  |      |
| Vacuum party                   | Vacuum cleaner               | Vacuums Party House           |  todo  |      |
| Industrial palletizing         | UR10 Suction                 | Palletizing                   |  todo  |      |
