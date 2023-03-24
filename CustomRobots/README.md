# CUSTOM ROBOT PACKAGE
This directory is entirely a ROS2 package with its CMakeLists.txt and package.xml. Every robot's resources directories will be stored in `/home/ws/install/custom_robots/share/custom_robots` after building the workspace and so the package named in every xml, xacro, urdf file muste be **custom_robots**.

### Build a new Robot
In order to create a knew robot and for it to be succesfully built open CMakeLists.txt and add the necessary resources in the following lines:
~~~
# find dependencies
set(PROJECT_DEPENDENCIES
  ament_cmake
  ...
        <------ add any dependencies that your robot will need
)

-----/-/-/-----

install(DIRECTORY
  ...
        <------ add the directories that contain the necessary 
                resources for your robot (urdf, rviz, launch, meshes, models etc.)

  DESTINATION share/${PROJECT_NAME}
)
~~~
