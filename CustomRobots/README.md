# CUSTOM ROBOT PACKAGE
This directory is entirely a ROS2 package with its CMakeLists.txt and package.xml. Every robot's resources directories will be stored in `/home/ws/install/custom_robots/share/custom_robots` after building the workspace and so the package named in every xml, xacro, urdf file muste be **custom_robots**.

### BUILD NEW ROBOT
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

### GAZEBO CAMERA

Place gzclient camera in a fixed position of the world adding to the `.world` file:
~~~
<gui fullscreen=1>
  <camera name='user_camera'>
    <pose >X Y Z ROLL PITCH YAW</pose>
    <view_controller>orbit</view_controller>
    <projection_type>perspective</projection_type>
  </camera>
</gui>
~~~
- Replace X Y Z ROLL PITCH YAW with the world's position you want the camera to be set

Make the gzclient camera follow a model adding to the `.world` file:
~~~
<gui fullscreen=1>
  <camera name="user_camera">
    <track_visual>
      <name>MODEL_NAME</name>
      <static>true</static>
      <use_model_frame>true</use_model_frame>
      <xyz>X Y Z</xyz>
      <inherit_yaw>true</inherit_yaw>
    </track_visual>
  </camera>
</gui>
~~~
- Replace MODEL_NAME with the name of the model you want the camara to follow
- Replace X Y Z with the relative coordinates to the model you want the camera to be set