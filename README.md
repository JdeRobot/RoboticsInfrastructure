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
- The world name defined inside the .world file must be "default":
  ```xml
  <?xml version="1.0" ?>
  <sdf version="1.10">
    <world name="default">
      .....
    </world>
  </sdf>
  ```

## How to add a new launcher

- To test the new launcher you will have to create a new RADI (or BTDI in BT Studio) with the Robotics Infrastructure flag (-i) set to your branch name.

### Gazebo Classic: **Legacy**

- Add the python ros launcher inside the Launchers directory using a clear and simple name (for example the same as the world or the exercise).

### Gazebo Harmonic

- Add the python ros launcher inside the Launchers directory using a clear and simple name (for example the same as the world or the exercise).
- Any additional launcher must be located inside a subdirectory inside Launchers that has the same name as the launcher (except the launch.py).
- The visualization configuration for Gazebo Harmonic must be located in the visualization folder inside Launchers with the name being the same as the launcher but replacing the .launch.py extension for .config.

## How to add a new universe

Go to the **database** branch. That branch is the one used as a submodule for Robotics Academy. To test it locally (in Robotics Academy or BT Studio) you must have the branch with the updated database selected and the execute the develop script in either application, this will mount your database into the docker container. 
