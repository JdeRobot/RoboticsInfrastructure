# RoboticsInfrastructure

Robots and tools useful for us and not included in the official ROS or Gazebo packages.

## How to contribute

**First of all** you have to know the infrastructure where you will develop your code:

- Gazebo version,
- ROS version
- Python version (if you develop in Python).

**This guide is only used if you cannot create the universes, worlds or tools using the graphical interface provided in Robotics Academy**.

## How to add a new universe

To create the entry in **database/universes.sql** you need to add the following things in the table **universes**.

To know where this is found search for the following line:

```sql
COPY public.universes (id, name, world_id, robot_id) FROM stdin;
```

And add a new line just below the last entry but above this:

```sql
\.
```

A universe entry in the database must include the following data:

- ```id```: it must be one more than the one above, it starts at 1.
- ```name```: name to display on the universe list
- ```world_id```: id of the world for this exercise, if there is no world put **0**. To know how to add a new World go to the section [How to add a new world](#how-to-add-a-new-world).
- ```robot_id```: id of the robot for this exercise, must be **0** until this feature works.

## How to add a new world

To create the entry in **database/universes.sql** you need to add the following things in the table **worlds**.

To know where this is found search for the following line:

```sql
COPY public.worlds (id, name, launch_file_path, tools_config, ros_version, type, start_pose) FROM stdin;
```

And add a new line just below the last entry but above this:

```sql
\.
```

A world entry in the database must include the following data:

- ```id```: it must be one more than the one above, it starts at 0.
- ```name```: name to display on the world list
- ```launch_file_path```: path to the launcher inside the docker. The Launcher folder is found in **/opt/jderobot/Launchers**.
- ```tools_config```: Json string with the desired tools config. If the exercise uses Gazebo Harmonic you must put add the config for the simulator GUI that is often found in **/opt/jderobot/Launchers/visualization**. If no config is needed use **None**.
- ```ros_version```: must be **ROS2**.
- ```type```: type of world, must be one of the following: **gz**, **none** or **physical**. The **gazebo** tag is for legacy Gazebo Classic universes and must not be used for new ones.
- ```start_pose```: start location of the robot: **{X,Y,Z,Roll,Pitch,Yaw}**. If the robot is not spawn separately, it can be {0,0,0,0,0,0}

## How to add a new robot: DOES NOT WORK

To create the entry in **database/universes.sql** you need to add the following things in the table **robots**.

To know where this is found search for the following line:

```sql
COPY public.robots (id, name, launch_file_path) FROM stdin;
```

And add a new line just below the last entry but above this:

```sql
\.
```

A robot entry in the database must include the following data:

- ```id```: it must be one more than the one above, it starts at 0.
- ```name```: name to display on the robot list
- ```launch_file_path```: path to the launcher inside the docker. The Launcher folder is found in **/opt/jderobot/Launchers/robots**.
 
## How to add a new tool:

To create the entry in **database/universes.sql** you need to add the following things in the table **tools**.

To know where this is found search for the following line:

```sql
COPY public.tools (name, base_config) FROM stdin;
```

And add a new line just below the last entry but above this:

```sql
\.
```

A robot entry in the database must include the following data:

- ```name```: name of the tool. Must be unique
- ```base_config```: Json string with the desired base config.