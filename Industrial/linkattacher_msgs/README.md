<!--
# ===================================== COPYRIGHT ===================================== #
#                                                                                       #
#  IFRA (Intelligent Flexible Robotics and Assembly) Group, CRANFIELD UNIVERSITY        #
#  Created on behalf of the IFRA Group at Cranfield University, United Kingdom          #
#  E-mail: IFRA@cranfield.ac.uk                                                         #
#                                                                                       #
#  Licensed under the Apache-2.0 License.                                               #
#  You may not use this file except in compliance with the License.                     #
#  You may obtain a copy of the License at: http://www.apache.org/licenses/LICENSE-2.0  #
#                                                                                       #
#  Unless required by applicable law or agreed to in writing, software distributed      #
#  under the License is distributed on an "as-is" basis, without warranties or          #
#  conditions of any kind, either express or implied. See the License for the specific  #
#  language governing permissions and limitations under the License.                    #
#                                                                                       #
#  IFRA Group - Cranfield University                                                    #
#  AUTHORS: Mikel Bueno Viso - Mikel.Bueno-Viso@cranfield.ac.uk                         #
#           Dr. Seemal Asif  - s.asif@cranfield.ac.uk                                   #
#           Prof. Phil Webb  - p.f.webb@cranfield.ac.uk                                 #
#                                                                                       #
#  Date: May, 2023.                                                                     #
#                                                                                       #
# ===================================== COPYRIGHT ===================================== #

# ======= CITE OUR WORK ======= #
# You can cite our work with the following statement:
# IFRA-Cranfield (2023) Gazebo-ROS2 Link Attacher. URL: https://github.com/IFRA-Cranfield/IFRA_LinkAttacher.
-->

<div id="top"></div>



<br />
<div align="center">

  <h2 align="center">IFRA_LinkAttacher - Gazebo-ROS2 Plugin</h2>

  <p align="center">
    IFRA (Intelligent Flexible Robotics and Assembly) Group
    <br />
    Centre for Robotics and Assembly
    <br />
    Cranfield University
  </p>
</div>

<br />

## ABOUT

### Intelligent Flexible Robotics and Assembly Group

The IFRA (Intelligent Flexible Robotics and Assembly) Group is part of the Centre for Robotics and Assembly at Cranfield University.

IFRA Group pushes technical boundaries. At IFRA we provide high tech automation & assembly solutions, and we support smart manufacturing with Smart Industry technologies and solutions. Flexible Manufacturing Systems (FMS) are a clear example. They can improve overall operations and throughput quality by adapting to real-time changes and situations, supporting and pushing the transition towards flexible, intelligent and responsive automation, which we continuously seek and support.

The IFRA Group undertakes innovative research to design, create and improve Intelligent, Responsive and Flexible automation & assembly solutions, and this series of GitHub repositories provide background information and resources of how these developments are supported.

__SOCIAL MEDIA__:

IFRA-Cranfield:
- YouTube: https://www.youtube.com/@IFRACranfield
- LinkedIn: https://www.linkedin.com/in/ifra-cranfield/

Centre for Robotics and Assembly:
- Instagram: https://www.instagram.com/cranfieldrobotics/
- Facebook: https://www.facebook.com/cranfieldunirobotics/
- YouTube: https://www.youtube.com/@CranfieldRobotics
- LinkedIn: https://www.linkedin.com/company/cranfieldrobotics/
- Website: https://www.cranfield.ac.uk/centres/centre-for-robotics-and-assembly 


### IFRA_LinkAttacher Repository

The IFRA_LinkAttacher repository contains 2 different ROS2 packages, which enable the attachment of 2 different entity links in Gazebo. This attachment is done through a simple ROS2/Gazebo plugin, and can be used for many applications in a Gazebo simulation environment. 

The plugin has been designed with the main purpose of simulating object pick and place tasks using Robot Manipulators in Gazebo. The link attachment/detachment feature is available through a ROS2 Service Server, which creates a temporary fixed joint between two links for the "ATTACH" request, and removes the previously generated joint for the "DETACH" service. Thanks to this functionality, objects can be easily attached to any end-effector and pick/place tasks can be simulated in Gazebo-ROS2.

DEVELOPMENT: For the design of the IFRA_LinkAttacher ROS2/Gazebo plugin, the design pattern of the working [gazebo_ros_state](https://github.com/ros-simulation/gazebo_ros_pkgs/blob/ros2/gazebo_ros/src/gazebo_ros_state.cpp) ROS2 plugin has been followed. The code has been modified/adapted for the main purpose of this new plugin (ATTACH/DETACH links), following the Gazebo API documentation for [gazebo::physics](http://osrf-distributions.s3.amazonaws.com/gazebo/api/11.0.0/group__gazebo__physics.html).

__VIDEO: Pick and Place Task - ROS2 Gazebo Simulation (UR3 + Robotiq 2f-85)__

[![Alt text](https://img.youtube.com/vi/t4L4VAfgqZw/0.jpg)](https://www.youtube.com/watch?v=t4L4VAfgqZw)

<br />

## INSTALLATION

Both packages in this repository have been developed, executed and tested in a Ubuntu 22.04 machine with ROS 2 Humble (the plugin has not been tested in other ROS2 distributions yet). It can be easily downloaded and installed by executing the following commands:

```sh
cd ~/dev_ws/src
git clone https://github.com/IFRA-Cranfield/IFRA_LinkAttacher.git
cd ~/dev_ws
colcon build
```

<br />

## USAGE

The IFRA_LinkAttacher ROS2-Gazebo plugin offers the link attachment/detachment feature though 2 different ROS2 Services, which can be called by executing the following commands:

```sh
# To ATTACH an OBJECT to a ROBOT's END-EFFECTOR:
ros2 service call /ATTACHLINK linkattacher_msgs/srv/AttachLink "{model1_name: 'model1', link1_name: 'link1', model2_name: 'model2', link2_name: 'link2'}"
# To DETACH the OBJECT from the END-EFFECTOR:
ros2 service call /DETACHLINK linkattacher_msgs/srv/DetachLink "{model1_name: 'model1', link1_name: 'link1', model2_name: 'model2', link2_name: 'link2'}"
```

Elements are defined as follows:
* model1 -> Name of the model/robot (defined in the robot .urdf). 
* link1 -> Name of the end-effector link that the object will be attached to.
* model2 -> Name of the object to be attached (defined in the object .urdf). 
* link2 -> Name of the object link.

__MAIN REQUIREMENT to execute the plugin: Gazebo .world file__

In order for the /ATTACHLINK and /DETACHLINK ROS2 services to be available in simulation, the LinkAttacher Plugin must be initialised in Gazebo. This is done by adding the following line to the Gazebo world file:
```
<plugin name="gazebo_link_attacher" filename="libgazebo_link_attacher.so"/>
```

An example of how the plugin is initialised in a world file can be found in the ros2_SimRealRobotControl GitHub repository [here](https://github.com/IFRA-Cranfield/ros2_SimRealRobotControl/blob/humble/ur3/ros2srrc_ur3_gazebo/worlds/ur3.world).

__EXAMPLE: Pick and place execution__

The source code for the pick and place video (UR3 + Robotiq 2f-85) shown [above](https://www.youtube.com/watch?v=t4L4VAfgqZw) and instructions about how different robot programs are generated (including object grasping) can be found in the ros2_SimRealRobotControl GitHub repository [here](https://github.com/IFRA-Cranfield/ros2_SimRealRobotControl/tree/humble/ros2srrc_execution).

<br />

## License

<p>
  Intelligent Flexible Robotics and Assembly Group
  <br />
  Created on behalf of the IFRA Group at Cranfield University, United Kingdom
  <br />
  E-mail: IFRA@cranfield.ac.uk 
  <br />
  <br />
  Licensed under the Apache-2.0 License.
  <br />
  You may obtain a copy of the License at: http://www.apache.org/licenses/LICENSE-2.0
  <br />
  <br />
  <a href="https://www.cranfield.ac.uk/">Cranfield University</a>
  <br />
  School of Aerospace, Transport and Manufacturing (SATM)
  <br />
    <a href="https://www.cranfield.ac.uk/centres/centre-for-robotics-and-assembly">Centre for Robotics and Assembly</a>
  <br />
  College Road, Cranfield
  <br />
  MK43 0AL, Bedfordshire, UK
  <br />
</p>

<br />

## Cite our work

<p>
  You can cite our work with the following statement:
  <br />
  IFRA-Cranfield (2023) Gazebo-ROS2 Link Attacher. URL: https://github.com/IFRA-Cranfield/IFRA_LinkAttacher.
</p>

<br />

## Contact

<p>
  Mikel Bueno Viso - Research Assistant in Intelligent Automation at Cranfield University
  <br />
  E-mail: Mikel.Bueno-Viso@cranfield.ac.uk
  <br />
  LinkedIn: https://www.linkedin.com/in/mikel-bueno-viso/
  <br />
  Profile: https://www.cranfield.ac.uk/people/mikel-bueno-viso-32884399
  <br />
  <br />
  Dr. Seemal Asif - Lecturer in Artificial Intelligence and Robotics at Cranfield University
  <br />
  E-mail: s.asif@cranfield.ac.uk
  <br />
  LinkedIn: https://www.linkedin.com/in/dr-seemal-asif-ceng-fhea-miet-9370515a/
  <br />
  Profile: https://www.cranfield.ac.uk/people/dr-seemal-asif-695915
  <br />
  <br />
  Professor Phil Webb - Professor of Aero-Structure Design and Assembly at Cranfield University
  <br />
  E-mail: p.f.webb@cranfield.ac.uk
  <br />
  LinkedIn: https://www.linkedin.com/in/phil-webb-64283223/
  <br />
  Profile: https://www.cranfield.ac.uk/people/professor-phil-webb-746415 
  <br />
</p>