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
#           Dr. Seemal Asif  - s.asif@cranfield.ac.uk                                   #
#           Prof. Phil Webb  - p.f.webb@cranfield.ac.uk                                 #
#                                                                                       #
#  Date: June, 2024.                                                                    #
#                                                                                       #
# ===================================== COPYRIGHT ===================================== #

# ======= CITE OUR WORK ======= #
# You can cite our work with the following statement:
# IFRA-Cranfield (2023) ROS 2 Sim-to-Real Robot Control. URL: https://github.com/IFRA-Cranfield/ros2_SimRealRobotControl.

# robot.py
# This CLIENT executes Robot Movements, by calling the following ROS2 Actions:
#   - /Robmove allows the user to move the robot to a specific End-Effector pose.
#   - /Move allows the user to execute a specific robot movement: Cartesian-Space, Joint-Space, Single Joint, Rotation...

# ===== IMPORT REQUIRED COMPONENTS ===== #
# System:
import time

# Required to include ROS2 and its components:
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

# Import /Move and /RobMove ROS2 Actions:
from ros2srrc_data.action import Move
from ros2srrc_data.action import Robmove

# Global Variable -> RES:
RES = {}
RES["Success"] = False
RES["Message"] = "null"
RES["ExecTime"] = -1.0

# =============================================================================== #
# /RobMove ACTION CLIENT:


class RobMoveCLIENT(Node):

    # node_name/action_name default to the original hardcoded values so any
    # existing caller doing RobMoveCLIENT() keeps working unchanged, a robot
    # with more than one arm passes a distinct node_name/action_name per arm
    # instead (see RBT below)
    def __init__(self, node_name="ros2srrc_RobMove_Client", action_name="/Robmove"):

        super().__init__(node_name)
        self._action_client = ActionClient(self, Robmove, action_name)
        self.action_name = action_name

        print(f"[CLIENT - robot.py]: Initialising ROS2 {action_name} Action Client!")
        print(
            f"[CLIENT - robot.py]: Waiting for {action_name} ROS2 ActionServer to be available..."
        )

        self._action_client.wait_for_server()

        print(f"[CLIENT - robot.py]: {action_name} ACTION SERVER detected, ready!")
        print("")
        print("")

    def send_goal(self, TYPE, SPEED, TARGET_POSE):

        goal_msg = Robmove.Goal()
        goal_msg.type = TYPE
        goal_msg.speed = SPEED
        goal_msg.x = TARGET_POSE.x
        goal_msg.y = TARGET_POSE.y
        goal_msg.z = TARGET_POSE.z
        goal_msg.qx = TARGET_POSE.qx
        goal_msg.qy = TARGET_POSE.qy
        goal_msg.qz = TARGET_POSE.qz
        goal_msg.qw = TARGET_POSE.qw

        self._send_goal_future = self._action_client.send_goal_async(goal_msg)
        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):

        self.goal_handle = future.result()

        if not self.goal_handle.accepted:
            print("[CLIENT - robot.py]: RobMove ACTION CALL -> GOAL has been REJECTED.")
            return

        print("[CLIENT - robot.py]: RobMove ACTION CALL -> GOAL has been ACCEPTED.")

        self._get_result_future = self.goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):

        global RES

        RESULT = future.result().result
        RES["Success"] = RESULT.success
        RES["Message"] = RESULT.message


# =============================================================================== #
# /Move ACTION CLIENT:


class MoveCLIENT(Node):

    def __init__(self, node_name="ros2srrc_Move_Client", action_name="/Move"):

        super().__init__(node_name)
        self._action_client = ActionClient(self, Move, action_name)
        self.action_name = action_name

        print(f"[CLIENT - robot.py]: Initialising ROS2 {action_name} Action Client!")
        print(
            f"[CLIENT - robot.py]: Waiting for {action_name} ROS2 ActionServer to be available..."
        )

        self._action_client.wait_for_server()

        print(f"[CLIENT - robot.py]: {action_name} ACTION SERVER detected, ready!")
        print("")

    def send_goal(self, ACTION):

        goal_msg = Move.Goal()
        goal_msg.action = ACTION.action
        goal_msg.speed = ACTION.speed
        goal_msg.movej = ACTION.movej
        goal_msg.mover = ACTION.mover
        goal_msg.movel = ACTION.movel
        goal_msg.moverot = ACTION.moverot
        goal_msg.moverp = ACTION.moverp
        goal_msg.moveg = ACTION.moveg

        self._send_goal_future = self._action_client.send_goal_async(goal_msg)
        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):

        self.goal_handle = future.result()

        if not self.goal_handle.accepted:
            print("[CLIENT - robot.py]: Move ACTION CALL -> GOAL has been REJECTED.")
            return

        print("[CLIENT - robot.py]: Move ACTION CALL -> GOAL has been ACCEPTED.")

        self._get_result_future = self.goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):

        global RES

        RESULT = future.result().result
        RES["Message"] = RESULT.result

        if "FAILED" in RES["Message"]:
            RES["Success"] = False
        else:
            RES["Success"] = True


# =============================================================================== #
# ROBOT class, to execute any robot movement:


class RBT:

    # suffix, move_action and robmove_action let a robot with more than one
    # arm create one RBT per arm, each pointed at that arm's own action
    # servers (see xlerobot_home's HAL.py), left at their defaults this is
    # the exact same single-robot behaviour every other exercise already
    # relies on. use_move=False skips connecting to /Move entirely, useful
    # when that action server was never brought up for this robot, otherwise
    # this call blocks forever in MoveCLIENT's wait_for_server()
    def __init__(
        self,
        suffix="",
        move_action="/Move",
        robmove_action="/Robmove",
        use_move=True,
    ):

        # Initialise /Move and /RobMove Action Clients:
        self.MoveClient = (
            MoveCLIENT(f"ros2srrc_Move_Client{suffix}", move_action)
            if use_move
            else None
        )
        self.RobMoveClient = RobMoveCLIENT(
            f"ros2srrc_RobMove_Client{suffix}", robmove_action
        )

        self.EXECUTING = ""

    def Move_EXECUTE(self, ACTION):

        if self.MoveClient is None:
            raise RuntimeError(
                "This RBT was created with use_move=False, /Move is not available"
            )

        global RES
        self.EXECUTING = "Move"

        T_start = time.time()

        # Initialise RES:
        RES["Success"] = False
        RES["Message"] = "null"
        RES["ExecTime"] = -1.0

        self.MoveClient.send_goal(ACTION)
        while rclpy.ok():
            rclpy.spin_once(self.MoveClient)

            if RES["Message"] != "null":
                break

        print("[CLIENT - robot.py]: Move ACTION EXECUTED -> Result: " + RES["Message"])
        print("")

        T_end = time.time()
        T = round((T_end - T_start), 4)
        RES["ExecTime"] = T

        self.EXECUTING = ""
        return RES

    def RobMove_EXECUTE(self, TYPE, SPEED, POSE):

        global RES
        self.EXECUTING = "RobMove"

        T_start = time.time()

        # Initialise RES:
        RES["Success"] = False
        RES["Message"] = "null"
        RES["ExecTime"] = -1.0

        self.RobMoveClient.send_goal(TYPE, SPEED, POSE)
        while rclpy.ok():
            rclpy.spin_once(self.RobMoveClient)

            if RES["Message"] != "null":
                break

        print(
            "[CLIENT - robot.py]: RobMove ACTION EXECUTED -> Result: " + RES["Message"]
        )
        print("")

        T_end = time.time()
        T = round((T_end - T_start), 4)
        RES["ExecTime"] = T

        self.EXECUTING = ""
        return RES

    def CANCEL(self):

        print("[CLIENT - robot.py]: MOVEMENT CANCEL REQUEST. Stopping robot...")

        try:
            if self.EXECUTING == "Move":
                self.MoveClient.goal_handle.cancel_goal_async()
            elif self.EXECUTING == "RobMove":
                self.RobMoveClient.goal_handle.cancel_goal_async()
            else:
                None
        except AttributeError:
            pass

        print("[CLIENT - robot.py]: MOVEMENT CANCEL REQUEST. Robot stopped.")
        print("")
