#!/usr/bin/env python3
"""Real Robotiq 2F-85 on a UR arm served as the simulated gripper_controller."""

import glob
import threading
import time

import rclpy
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node
from sensor_msgs.msg import JointState

from ur5_bridge.robotiq import MOVING, RtuGripper, UrcapGripper

JOINT = "robotiq_85_left_knuckle_joint"

# Upper limit of JOINT in the URDF, the HAL maps 0-100 % onto it
CLOSED_POSITION = 0.80285

# Serial ports tried in auto mode, the e-Series tool flange first
RTU_PORTS = ["/tmp/ttyUR", "/dev/ttyUSB*", "/host_dev/ttyUSB*"]


class GripperNode(Node):
    def __init__(self):
        # Named like the simulated controller so the HAL finds its parameters
        super().__init__("gripper_controller")

        self.declare_parameter("joints", [JOINT])
        self.declare_parameter("robot_ip", "192.168.56.101")
        # auto, urcap, rtu or none
        self.declare_parameter("interface", "auto")
        self.declare_parameter("rtu_port", "auto")
        self.declare_parameter("speed", 255)
        self.declare_parameter("force", 150)
        self.declare_parameter("rate", 10.0)

        self.robot_ip = self.get_parameter("robot_ip").value
        self.interface = self.get_parameter("interface").value
        self.rtu_port = self.get_parameter("rtu_port").value
        self.speed = self.get_parameter("speed").value
        self.force = self.get_parameter("force").value

        self.gripper = None
        self.lock = threading.Lock()
        self.position = 0.0
        self.group = ReentrantCallbackGroup()

        self.joint_pub = self.create_publisher(JointState, "/joint_states", 10)
        self.create_timer(
            1.0 / self.get_parameter("rate").value,
            self.publish_joint_state,
            callback_group=self.group,
        )

        self.action_server = ActionServer(
            self,
            FollowJointTrajectory,
            "/gripper_controller/follow_joint_trajectory",
            execute_callback=self.execute,
            goal_callback=lambda goal: GoalResponse.ACCEPT,
            cancel_callback=lambda goal: CancelResponse.ACCEPT,
            callback_group=self.group,
        )

        if self.interface == "none":
            self.get_logger().info("no gripper configured")
        else:
            threading.Thread(target=self.connect, daemon=True).start()

    def candidates(self):
        if self.interface in ("auto", "urcap"):
            yield lambda: UrcapGripper(self.robot_ip)
        if self.interface in ("auto", "rtu"):
            if self.rtu_port == "auto":
                ports = [p for pattern in RTU_PORTS for p in sorted(glob.glob(pattern))]
            else:
                ports = [self.rtu_port]
            for port in ports:
                yield lambda port=port: RtuGripper(port)

    def connect(self):
        warned = False
        while rclpy.ok() and self.gripper is None:
            for open_gripper in self.candidates():
                try:
                    gripper = open_gripper()
                except OSError:
                    continue
                try:
                    if not gripper.active():
                        self.activate(gripper)
                except OSError:
                    gripper.close()
                    continue
                with self.lock:
                    self.gripper = gripper
                self.get_logger().info(f"Robotiq gripper ready on {gripper.where}")
                return
            if not warned:
                self.get_logger().warn(
                    "Robotiq gripper not found, is the Robotiq URCap installed "
                    "and the gripper powered? Retrying"
                )
                warned = True
            time.sleep(3.0)

    def activate(self, gripper):
        self.get_logger().info("activating the gripper, the fingers open and close")
        gripper.reset()
        gripper.activate()
        deadline = time.monotonic() + 15.0
        while not gripper.active():
            if time.monotonic() > deadline:
                raise OSError("gripper activation timed out")
            time.sleep(0.2)

    def lost(self, error):
        with self.lock:
            # Only the first caller reconnects
            if self.gripper is None:
                return
            self.gripper.close()
            self.gripper = None
        self.get_logger().error(f"Robotiq gripper lost: {error}")
        threading.Thread(target=self.connect, daemon=True).start()

    def publish_joint_state(self):
        if self.gripper is not None:
            try:
                with self.lock:
                    position, _, _ = self.gripper.status()
                self.position = position / 255.0 * CLOSED_POSITION
            except (OSError, AttributeError) as e:
                self.lost(e)
        # Published even without a gripper so MoveIt and the TF tree are complete
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = [JOINT]
        msg.position = [self.position]
        self.joint_pub.publish(msg)

    def execute(self, goal_handle):
        result = FollowJointTrajectory.Result()
        trajectory = goal_handle.request.trajectory

        if JOINT not in trajectory.joint_names:
            goal_handle.abort()
            result.error_code = FollowJointTrajectory.Result.INVALID_JOINTS
            result.error_string = f"expected joint {JOINT}"
            return result

        if not trajectory.points:
            goal_handle.succeed()
            return result

        deadline = time.monotonic() + (0.0 if self.interface == "none" else 20.0)
        while self.gripper is None and time.monotonic() < deadline:
            time.sleep(0.2)
        if self.gripper is None:
            goal_handle.abort()
            result.error_code = FollowJointTrajectory.Result.INVALID_GOAL
            result.error_string = (
                "no gripper configured, UR_GRIPPER is none"
                if self.interface == "none"
                else "Robotiq gripper not connected"
            )
            self.get_logger().error(result.error_string)
            return result

        target = trajectory.points[-1].positions[trajectory.joint_names.index(JOINT)]
        register = round(min(max(target / CLOSED_POSITION, 0.0), 1.0) * 255)

        try:
            with self.lock:
                # An emergency stop cuts the gripper power and leaves it deactivated
                if not self.gripper.active():
                    self.activate(self.gripper)
                self.gripper.move(register, self.speed, self.force)
            # The status reads as moving only once the new goal is taken
            time.sleep(0.1)
            done = False
            deadline = time.monotonic() + 5.0
            while time.monotonic() < deadline:
                if goal_handle.is_cancel_requested:
                    goal_handle.canceled()
                    return result
                with self.lock:
                    _, obj, fault = self.gripper.status()
                if obj != MOVING:
                    done = True
                    break
                time.sleep(0.05)
        except (OSError, AttributeError) as e:
            self.lost(e)
            goal_handle.abort()
            result.error_code = FollowJointTrajectory.Result.INVALID_GOAL
            result.error_string = f"Robotiq gripper lost: {e}"
            return result

        if not done:
            goal_handle.abort()
            result.error_code = FollowJointTrajectory.Result.GOAL_TOLERANCE_VIOLATED
            result.error_string = "the Robotiq gripper did not finish the move"
            self.get_logger().error(result.error_string)
            return result

        if fault:
            goal_handle.abort()
            result.error_code = FollowJointTrajectory.Result.PATH_TOLERANCE_VIOLATED
            result.error_string = f"Robotiq gripper fault {fault:#x}"
            self.get_logger().error(result.error_string)
            return result

        # Stopping on an object before the target is a successful grasp
        goal_handle.succeed()
        result.error_code = FollowJointTrajectory.Result.SUCCESSFUL
        return result


def main(args=None):
    rclpy.init(args=args)
    node = GripperNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
