# RoboticsInfrastructure

Robots and tools useful for us and not included in the official ROS or Gazebo packages.

## How to contribute

**First of all** you have to know the infrastructure where you will develop your code:

- Gazebo version,
- ROS version
- Python version (if you develop in Python).

## How to add new models

- Upload the new model files to the CustomRobots directory.
- If necessary update the install section (starts in line 78) in the CMakeLists.txt file to acomodate the new directories following the same schema as the other entries.
- To test the new models you will have to create a new RADI (or BTDI in BT Studio) with the Robotics Infrastructure flag (-i) set to your branch name.

## How to add a new world

- Add the world file inside the Worlds directory using a clear and simple name.
- You will also need to create a launcher for each world and add it to the database.
- To test the new world you will have to create a new RADI (or BTDI in BT Studio) with the Robotics Infrastructure flag (-i) set to your branch name.

## How to add a new launcher

- To test the new launcher you will have to create a new RADI (or BTDI in BT Studio) with the Robotics Infrastructure flag (-i) set to your branch name.

### Gazebo Classic

- Add the python ros launcher inside the Launchers directory using a clear and simple name (for example the same as the world or the exercise).

### Gazebo Harmonic

- Add the python ros launcher inside the Launchers directory using a clear and simple name (for example the same as the world or the exercise).
- Any additional launcher must be located inside a subdirectory inside Launchers that has the same name as the launcher (except the launch.py).
- The visualization configuration for Gazebo Harmonic must be located in the visualization folder inside Launchers with the name being the same as the launcher but replacing the .launch.py extension for .config.

## How to add a new universe

To add a new universe to the RoboticsAcademy database so that it can be included in a new exercise or one already created within RoboticsInfrastructure, the following steps must be performed:

1) Create a new branch in both RoboticsAcademy and RoboticsInfrastructure with the name format **<exercise-name>-new-universe**, to avoid conflicts with the main branch (humble-devel). It is recommended that both branches have the same name for better readability and organization.

2) Access the file **RoboticsAcademy/database/exercises/db.sql** and add a new entry within the universe list as explained below, respecting the indentation between columns.

To better understand how to do this, I have chosen as an example the element with 'id 56' from the **public.exercises_universes** table, corresponding to the exercise with 'id 1' (follow_line) defined in the **public.exercises** table and the universe with 'id 52', defined in the **public.universes** table located in the **RoboticsInfrastructure/database/universes.sql** file.

```sh
# FILE RoboticsAcademy/database/exercises/db.sql
COPY public.exercises_universes (id, exercise_id, universe_id, is_default) FROM stdin;
...
56	1	52	False
...
id	exercise_id	universe_id	is_default
\.
```

Where:

- ```id```: Unique identifier for each exercise-universe relationship, that is, the position in the list where it is declared. In this case, if the last id is 56, the new one to add should be 57.

- ```exercise_id```: Key that refers to which exercise the new universe is being assigned to (column 'id' of the **public.exercises** table). In this case, the universe with 'id 56' is used in the exercise with 'id 1' (follow_line), but if we wanted to use it in another exercise, such as obstacle_avoidance, the value of the exercise_id column for this new universe should be 8.

- ```universe_id```: Indicates which universe will launch the exercise (column 'id' of the **public.universes** table, located in the **RoboticsInfrastructure/database/universes.sql** file).

- ```is_default```: Indicates whether this new universe should appear by default when launching the exercise (**True** if it is the default universe, and **False** if it is not).

3) Access the file **RoboticsInfrastructure/database/universes.sql** and add a new entry within the list of universes (table **public.universes**) in the manner explained below and respecting the indentation between columns.

```sh
# FILE RoboticsInfrastructure/database/universes.sql
COPY public.universes (id, name, world_id, robot_id) FROM stdin;
...
52 	Montreal Circuit Classic	52	0
...
id 	name	world_id	robot_id
\.
```

Where:

- ```id```: Unique identifier for each exercise-universe relationship, that is, the position in the list where it is declared. In this case, if the last id is 52, the new one to add should be 53.

- ```name```: Indicates the name with which the universe will appear within the drop-down list of selectable universes of the corresponding exercise.

- ```world_id```: Refers to the id of the **public.exercises_universes** table in the **RoboticsAcademy/database/exercises/db.sql** file, which indicates the exercise in which this new universe will be included.

- ```robot_id```: Null value, so its value must always be 0.

4) And finally, add the new universe to the **public.worlds** table of the **RoboticsInfrastructure/database/universes.sql** file, whose 'id' column must have the same value as the 'world_id' column of the **public.universes** table of the **RoboticsInfrastructure/database/universes.sql** file ('world_id' = 'id').

```sh
# FILE RoboticsInfrastructure/database/universes.sql
COPY public.worlds (id, name, launch_file_path, tools_config, ros_version, type, start_pose) FROM stdin;
...
52	Montreal Circuit Classic	/opt/jderobot/Launchers/montreal_circuit_classic.launch.py	None	ROS2	gazebo	{0.0,0.0,0.0,0.0,0.0,0.0}
...
id	name	/opt/jderobot/Launchers/new_universe.launch.py	None / {"gzsim":"/opt/jderobot/Launchers/visualization/new_universe.config"}	ROS2	gazebo / gz	{0.0,0.0,0.0,0.0,0.0,0.0}
\.
```
