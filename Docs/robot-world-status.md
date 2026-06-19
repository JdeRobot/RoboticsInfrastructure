# Table of robots, worlds and universes

## Robots

| Robot ID           |                                         Launch path                                          |       Entity name        |                   Configs available                    | URDF/SDF | Notes                    |
| ------------------ | :------------------------------------------------------------------------------------------: | :----------------------: | :----------------------------------------------------: | :------: | ------------------------ |
| Ur5                |                      /home/ws/src/CustomRobots/ur5/launch/ur5.launch.py                      |       ur5_robotiq        |                                                        |   URDF   | Broken Reset             |
| F1 car             |                       /home/ws/src/CustomRobots/f1/launch/f1.launch.py                       |            f1            |      mode=(holo/ackermann) sensor=(camera/laser)       |   URDF   |                          |
| Autonomous car     |           /home/ws/src/CustomRobots/autonomous_car/launch/autonomous_car.launch.py           |      autonomous_car      | mode=(holonomic/ackermann) sensor=(camera/laser/lidar) |   URDF   |                          |
| Vacuum cleaner     |           /home/ws/src/CustomRobots/vacuum_cleaner/launch/vacuum_cleaner.launch.py           |      vacuum_cleaner      |                 sensor=(camera/laser)                  | URDF/SDF | Broken bumper in URDF    |
| Quadrotor          |                /home/ws/src/CustomRobots/quadrotor/launch/quadrotor.launch.py                |        quadrotor         |               sensor=(camera) namespace                | URDF/SDF | Does not fly             |
| Rover 4wd          |                /home/ws/src/CustomRobots/quadrotor/launch/rover_4wd.launch.py                |        rover_4wd         |               noise=(none/low/med/high)                |   URDF   |                          |
| Logistic Holonomic | /home/ws/src/CustomRobots/logistic_holonomic_robot/launch/logistic_holonomic_robot.launch.py | logistic_holonomic_robot |                                                        | URDF/SDF | Ball joint fails in URDF |
| Logistic Ackermann | /home/ws/src/CustomRobots/logistic_ackermann_robot/launch/logistic_ackermann_robot.launch.py | logistic_ackermann_robot |                                                        |   URDF   |                          |
| TurtleBot 2        |               /home/ws/src/CustomRobots/Turtlebot2/launch/turtlebot2.launch.py               |        turtlebot2        |                 sensor=(camera/stereo)                 |   URDF   |                          |
| TurtleBot 3        |               /home/ws/src/CustomRobots/Turtlebot2/launch/turtlebot2.launch.py               |        turtlebot3        |               noise=(none/low/med/high)                |   URDF   |                          |

## Worlds

"Robot included" means that the world launcher only launches the world and not the robot.

| World ID                             |           Launch path (/opt/jderobot/Launchers)           |          Spawn point           | Robot included | 🟧 Gazebo Harmonic | Notes        |
| ------------------------------------ | :-------------------------------------------------------: | :----------------------------: | :------------: | :----------------: | ------------ |
| 3d Reconstruction                    |                3d_reconstruction.launch.py                |          0,0,0,0,0,0           |       No       |         ok         |              |
| City Large                           |                   basic_city.launch.py                    |     0,0,0.1,0,0,-1.5529944     |       No       |         ok         |              |
| Autopark_line                        |                  autopark_line.launch.py                  |       -7,2.5,0.004,0,0,0       |       No       |         ok         |              |
| Autopark_battery                     |                autopark_battery.launch.py                 |       -7,2.5,0.004,0,0,0       |       No       |         ok         |              |
| Autopark_sideways                    |                autopark_sideways.launch.py                |       -7,2.5,0.004,0,0,0       |       No       |         ok         |              |
| Autoparking Gas Station: In battery  |          gas_station_battery_ackermann.launch.py          |                                |      Yes       |                    |              |
| Autoparking Gas Station: In line     |           gas_station_line_ackermann.launch.py            |                                |      Yes       |                    |              |
| Autoparking Gas Station: Parking lot |          gas_station_parking_ackermann.launch.py          |                                |      Yes       |                    |              |
| Follow Person                        |             follow_person_harmonic.launch.py              |      -1.0,10.0,0.1,0,0,0       |       No       |         ok         |              |
| Follow Person Teleop                 |          follow_person_teleop_harmonic.launch.py          |      -1.0,10.0,0.1,0,0,0       |       No       |         ok         |              |
| Laser Mapping Warehouse              |                  laser_mapping.launch.py                  |   14.25,-10.75,0.1,0,-0,3.14   |       No       |         ok         |              |
| Small Laser Mapping Warehouse        |               small_laser_mapping.launch.py               |          0,0,0,0,0,0           |       No       |         ok         |              |
| Simple Circuit                       |                 simple_circuit.launch.py                  | 53.462,-10.734,0.004,0,0,-1.57 |       No       |         ok         |              |
| Montmelo Circuit                     |                montmelo_circuit.launch.py                 |  27.18,-31.55,0,0,0.01,-3.12   |       No       |         ok         |              |
| Montreal Circuit                     |                montreal_circuit.launch.py                 |   -200.88,-90.72,0,0,0,-2.83   |       No       |         ok         |              |
| Nurburgring Circuit                  |               nurburgring_circuit.launch.py               |    -74.29,37.74,0,0,0,-0.51    |       No       |         ok         |              |
| Monaco Circuit                       |                 monaco_circuit.launch.py                  | -105.223,-70.77,-1.8,0,0,1.69  |       No       |         ok         |              |
| Spa Circuit                          |                   spa_circuit.launch.py                   |                                |      Yes       |                    |              |
| Obstacle Avoidance                   |              obstacle_avoidance_h.launch.py               |     0.04,0.68,0,0,0,-1.57      |       No       |         ok         |              |
| Rescue People                        |                  rescue_people.launch.py                  |         0,0,1.45,0,0,0         |       No       |         ok         |              |
| Warehouse 1                          |                   warehouse1.launch.py                    |         0,0,0.1,0,0,0          |       No       |         ok         |              |
| Warehouse 2                          |                   warehouse2.launch.py                    |         0,0,0.1,0,0,0          |       No       |         ok         |              |
| Restaurant                           |                   restaurant.launch.py                    |                                |      Yes       |                    |              |
| Small House                          |                   small_house.launch.py                   |         -1,1.5,0,0,0,0         |       No       |         ok         |              |
| Vacuums House Markers                |                 detailed_house.launch.py                  |       1,-1.5,0.43,0,0,0        |       No       |         ok         |              |
| Small House Roof                     |                small_house_roof.launch.py                 |         -1,1.5,0,0,0,0         |       No       |         ok         |              |
| Follow Road                          |                   follow_road.launch.py                   |     17.96,0.0,0.3,0,0,-2.0     |       No       |         ok         |              |
| Car Junction                         |                  car_junction.launch.py                   |      2.5,-30,0.1,0,0,1.57      |       No       |         ok         |              |
| Drone Gymkhana                       |                 drone_gymkhana.launch.py                  |    0.0,0.0,1.0,0.0,0.0,0.0     |       No       |         ok         |              |
| Tower Inspection                     |             power_tower_inspection.launch.py              |     -21.0,-4.0,1.45,0,0,0      |       No       |         ok         |              |
| Labyrinth Escape                     |                labyrinth_escape.launch.py                 |       -18,-8.5,0.3,0,0,0       |       No       |         ok         |              |
| Package delivery world               |                package_delivery.launch.py                 |    -1.0,-4.0,0.3,0,0,1.5729    |       No       |         ok         |              |
| Rover 4wd Warehouse                  |               rover_4wd_warehouse.launch.py               |         0,0,0.15,0,0,0         |       No       |         ok         |              |
| Pick And Place                       |                   pick_place.launch.py                    |         0,0,0.9,0,0,0          |       No       |         ok         | Reset broken |
| Machine Vision                       | machine_vision_harmonic/machine_vision_harmonic.launch.py |                                |      Yes       |

## Assets to review

- RoboticsInfrastructure/CustomRobots/drone_assets/models/car_color_beacon
- RoboticsInfrastructure/CustomRobots/drone_assets/plugins/

- RoboticsInfrastructure/CustomRobots/tello_phy/tello_ros/
- Is gz_ros2_control the same as gazebo_ros2_control

- RoboticsInfrastructure/Worlds/machine_vision.world
- RoboticsInfrastructure/Worlds/road_junction.world

ignition
