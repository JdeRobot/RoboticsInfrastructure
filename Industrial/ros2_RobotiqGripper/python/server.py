#!/usr/bin/python3

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

# IMPORT -> Required libraries:
import rclpy
from rclpy.node import Node
from ros2_robotiqgripper.srv import RobotiqGripper
import socket, time, re

# ===== INPUT PARAMETER ===== #
PARAM_IP = "0.0.0.0"
P_CHECK_IP = False

class ipPARAM(Node):
    
    def __init__(self):

        global PARAM_IP
        global P_CHECK_IP
        
        super().__init__('ros2_robotiq_ip_param')
        self.declare_parameter('IPAddress', "None")

        PARAM_IP = self.get_parameter('IPAddress').get_parameter_value().string_value
        
        if (PARAM_IP == "None"):

            print('IPAddress ROS2 Parameter was not defined for the ros2_robotiq Service Server.')
            exit()

        else:    
            print('IPAddress ROS2 Parameter received: ' + PARAM_IP)

        P_CHECK_IP = True

# Create NODE:
class serviceServer(Node):

    def __init__(self, IP):

        # Initialise ROS 2 Service Server:
        super().__init__('ros2_RobotiqGripper_ServiceServer')
        self.SERVICE = self.create_service(RobotiqGripper, "Robotiq_Gripper", self.ExecuteService)

        self.ip = IP

    def ExecuteService(self, request, response):

        # INITIALISE RESPONSE:
        response.success = False
        response.value = -1
        response.average = -1.0
        
        # TCP-IP + SOCKET settings:
        HOST = self.ip
        PORT = 63352
        
        # SOCKET COMMUNICATION:
        SCKT = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        SCKT.settimeout(3) # Timeout of 3 seconds.

        # OPEN socket:
        while True:
            try:
                SCKT.connect((HOST, PORT))
                break
            except TimeoutError:
                response.message = "ERROR: TCP-IP socket connection timed out! Please verify IP address and PORT."
                return(response)
            except ConnectionRefusedError:
                response.message = "ERROR: TCP-IP socket connection was refused! Please verify IP address and PORT."
                return(response)

        if request.action == "CLOSE":
            
            SCKT.sendall(b'SET POS 255\n')
            ignore = SCKT.recv(2**10)
            time.sleep(1.0)
            SCKT.sendall(b'GET POS\n')
            data = SCKT.recv(2**10)

            GripperPos_STR = int(re.search(r'\d+', str(data)).group())
            AVERAGE = round((float(GripperPos_STR)/255.0)*100.0, 2)
            
            response.success = True
            response.value = GripperPos_STR
            response.average = AVERAGE
            response.message = "CLOSE command successfully sent to Robotiq gripper. After execution, the gripper is -> " + str(AVERAGE) + "% CLOSED."
            return(response)

        elif request.action == "OPEN":
            
            SCKT.sendall(b'SET POS 0\n')
            ignore = SCKT.recv(2**10)
            time.sleep(1.0)
            SCKT.sendall(b'GET POS\n')
            data = SCKT.recv(2**10)

            GripperPos_STR = int(re.search(r'\d+', str(data)).group())
            AVERAGE = round((float(GripperPos_STR)/255.0)*100.0, 2)
            
            response.success = True
            response.value = GripperPos_STR
            response.average = AVERAGE
            response.message = "OPEN command successfully sent to Robotiq gripper. After execution, the gripper is -> " + str(AVERAGE) + "% CLOSED."
            return(response)

        else:
            response.message = "ERROR: Valid commands are OPEN/CLOSE. Please try again."
            return(response)

# =================== MAIN =================== #
def main(args=None):

    rclpy.init(args=args)

    # Get IP Address:PROGRAM
    global PARAM_IP
    global P_CHECK_IP

    paramNODE = ipPARAM()
    while (P_CHECK_IP == False):
        rclpy.spin_once(paramNODE)
    paramNODE.destroy_node()
    
    # Initialise NODE:
    GripperNode = serviceServer(PARAM_IP)
    print ("[ROS2 Robotiq Gripper]: ros2_RobotiqGripper_ServiceServer generated.")

    # Spin SERVICE:
    rclpy.spin(GripperNode)
    
    GripperNode.destroy_node
    rclpy.shutdown()

if __name__ == '__main__':
    main()


