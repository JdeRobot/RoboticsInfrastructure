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
#           Fahad Khan       - f.khan@cranfield.ac.uk                                   #
#           Dr. Seemal Asif  - s.asif@cranfield.ac.uk                                   #
#           Prof. Phil Webb  - p.f.webb@cranfield.ac.uk                                 #
#                                                                                       #
#  Date: May, 2024.                                                                     #
#                                                                                       #
# ===================================== COPYRIGHT ===================================== #

# ======= CITE OUR WORK ======= #
# You can cite our work with the following statement:
# IFRA-Cranfield (2024) ROS 2 Robotiq Gripper Driver. URL: https://github.com/IFRA-Cranfield/ros2_RobotiqGripper.

-->

<div id="top"></div>

<br />
<div align="center">

  <h2 align="center">IFRA-Cranfield/ros2_RobotiqGripper - ROS 2 Driver</h2>

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
- Facebook: https://www.facebook.com/cranfieldrobotics/
- YouTube: https://www.youtube.com/@CranfieldRobotics
- LinkedIn: https://www.linkedin.com/company/cranfieldrobotics/
- Website: https://www.cranfield.ac.uk/centres/centre-for-robotics-and-assembly 


### ros2_RobotiqGripper Repository

This ROS 2 package provides a convenient interface for controlling the Robotiq Gripper when connected to a Universal Robots (UR) robot arm. The driver utilizes the UR Robot's TCP-IP socket connectivity to establish communication with the gripper.

__Features__

- ROS 2 Service Interface: The driver encapsulates the gripper's open and close commands into ROS 2 services, allowing users to easily request gripper actions from within their ROS 2 environment. Additionally, information about the gripper's opening ratio is provided after each execution, enhancing control and monitoring capabilities.

- Tested Compatibility: The driver has been extensively tested with the Robotiq HandE gripper, ensuring reliable operation in real-world scenarios. Future plans include expanding support to encompass a broader range of Robotiq grippers, enhancing versatility and compatibility across different robotic applications.

__VIDEO: Pick and Place Task - UR3 Robot w/ Robotiq HandE Parallel Gripper__

Video Demonstration coming soon.

<br />

## INSTALLATION

The RobotiqGripper ROS 2 Package has been developed, executed and tested in a Ubuntu 22.04 machine with ROS 2 Humble. It can be easily downloaded and installed by executing the following commands:

```sh
cd ~/dev_ws/src
git clone https://github.com/IFRA-Cranfield/ros2_RobotiqGripper.git
cd ~/dev_ws
colcon build
```

<br />

## USAGE

Our driver offers the Robotiq Gripper OPEN/CLOSE feature through a unique ROS2 Service, which can be executed by executing the following commands:

```sh
# Execute the ROS 2 SERVICE SERVER:
ros2 run ros2_robotiqgripper server.py --ros-args -p IPAddress:="0.0.0.0"

# Execute the SERVICE (client):
ros2 service call /Robotiq_Gripper ros2_robotiqgripper/srv/RobotiqGripper "{action: 'CLOSE'}"
```

__INTEGRATION with the UR3 Robot__

Please do have a look at the [UR3-ROS 2 Cranfield Robotics Repository](https://github.com/IFRA-Cranfield/ur3_CranfieldRobotics) for a more detailed documentation of how the Robotiq ROS 2 Driver has been implemented to operate the Robotiq HandE gripper on a real UR3 Robot, using ROS 2.

- The gripper's SERVICE SERVER Node is launched within the Robot Bringup package's launch file, [here](https://github.com/IFRA-Cranfield/ur3_CranfieldRobotics/blob/main/ur3cranfield_bringup/launch/bringup_hande.launch.py).
- The gripper's SERVICE CLIENT Node is defined as a Python class [here](https://github.com/IFRA-Cranfield/ur3_CranfieldRobotics/blob/main/ur3cranfield_execution/robot/gripper.py), which is instantiated to operate the gripper inside a Python script [here](https://github.com/IFRA-Cranfield/ur3_CranfieldRobotics/blob/main/ur3cranfield_execution/robot/routines.py).

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
  IFRA-Cranfield (2024) ROS 2 Robotiq Gripper Driver. URL: https://github.com/IFRA-Cranfield/IFRA_LinkAttacher.
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
  Fahad Khan - Research Assistant in Intelligent Automation at Cranfield University
  <br />
  E-mail: Fahad.Khan@cranfield.ac.uk
  <br />
  LinkedIn: https://www.linkedin.com/in/fahad-khan-roboticist/
  <br />
  Profile: https://www.cranfield.ac.uk/people/fahad-khan-28766264
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