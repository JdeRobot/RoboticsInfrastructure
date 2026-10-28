#!/usr/bin/env python3
"""Watches the real UR arm, explains in the log why it does not move and
recovers it after a stop or a lost connection.

ur_robot_driver stays quiet when the robot never starts its control program,
trajectories are just aborted. After a power cycle or an emergency stop it
keeps the program as running while the robot is paused, so a trajectory
freezes forever and would resume on its own once the robot is back.
"""

import time

import rclpy
from controller_manager_msgs.srv import SwitchController
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile
from std_msgs.msg import Bool
from std_srvs.srv import Trigger
from ur_dashboard_msgs.msg import RobotMode, SafetyMode
from ur_dashboard_msgs.srv import IsInRemoteControl

ARM_CONTROLLER = "joint_trajectory_controller"

# Time the robot gets to start the program before warning
PROGRAM_TIMEOUT = 15.0

ROBOT_MODES = {
    RobotMode.POWER_OFF: "powered off, power it on from the pendant",
    RobotMode.POWER_ON: "powering on",
    RobotMode.IDLE: "powered on with the brakes locked, release them from the pendant",
    RobotMode.BOOTING: "booting",
    RobotMode.CONFIRM_SAFETY: "waiting for the safety configuration to be confirmed on the pendant",
    RobotMode.BACKDRIVE: "in backdrive mode",
}

# Any other safety mode stops the arm
SAFETY_OK = (SafetyMode.NORMAL, SafetyMode.REDUCED)

SAFETY_STOPS = {
    SafetyMode.PROTECTIVE_STOP: "protective stop, unlock it from the pendant",
    SafetyMode.SAFEGUARD_STOP: "safeguard stop",
    SafetyMode.SYSTEM_EMERGENCY_STOP: "system emergency stop",
    SafetyMode.ROBOT_EMERGENCY_STOP: "emergency stop button pressed",
    SafetyMode.VIOLATION: "safety violation",
    SafetyMode.FAULT: "safety fault",
}


class StatusNode(Node):
    def __init__(self):
        super().__init__("ur5_status")

        self.declare_parameter("headless_mode", True)
        self.headless = self.get_parameter("headless_mode").value

        self.robot_mode = None
        self.safety_mode = None
        self.program_running = False
        self.stopped = False
        self.waiting_since = time.monotonic()
        self.warned = False
        self.resending = False
        self.remote = None

        self.switch_client = self.create_client(
            SwitchController, "/controller_manager/switch_controller"
        )
        self.resend_client = self.create_client(
            Trigger, "/io_and_status_controller/resend_robot_program"
        )
        self.remote_client = self.create_client(
            IsInRemoteControl, "/dashboard_client/is_in_remote_control"
        )

        # The driver only publishes on change, a late subscriber needs the last value
        latched = QoSProfile(depth=1, durability=QoSDurabilityPolicy.TRANSIENT_LOCAL)
        self.create_subscription(
            RobotMode,
            "/io_and_status_controller/robot_mode",
            self.on_robot_mode,
            latched,
        )
        self.create_subscription(
            SafetyMode,
            "/io_and_status_controller/safety_mode",
            self.on_safety_mode,
            latched,
        )
        self.create_subscription(
            Bool,
            "/io_and_status_controller/robot_program_running",
            self.on_program,
            latched,
        )
        self.create_timer(1.0, self.check)

    def ready(self):
        return (
            self.robot_mode == RobotMode.RUNNING
            and self.safety_mode in SAFETY_OK
        )

    def on_robot_mode(self, msg):
        if msg.mode == self.robot_mode:
            return
        self.robot_mode = msg.mode
        if msg.mode == RobotMode.RUNNING:
            # The program can only start from here on
            self.waiting_since = time.monotonic()
            self.get_logger().info("robot powered on and brakes released")
        else:
            self.get_logger().warn(
                f"robot {ROBOT_MODES.get(msg.mode, f'in mode {msg.mode}')}"
            )
        self.update()

    def on_safety_mode(self, msg):
        if msg.mode == self.safety_mode:
            return
        self.safety_mode = msg.mode
        if msg.mode not in SAFETY_OK:
            reason = SAFETY_STOPS.get(msg.mode, f"safety mode {msg.mode}")
            self.get_logger().error(f"robot stopped, {reason}")
        self.update()

    def update(self):
        if self.robot_mode is None or self.safety_mode is None:
            return
        if not self.ready() and not self.stopped:
            # Aborts the frozen trajectory so it never resumes by surprise
            self.stopped = True
            self.switch(deactivate=[ARM_CONTROLLER])
        elif self.ready() and self.stopped:
            self.stopped = False
            self.recover()

    def recover(self):
        if not self.headless:
            self.get_logger().warn("robot back, press play on the pendant program")
            self.switch(activate=[ARM_CONTROLLER])
            return
        self.get_logger().info("robot back, sending the control program again")
        self.resending = True
        future = self.resend_client.call_async(Trigger.Request())
        future.add_done_callback(self.on_resent)

    def on_resent(self, future):
        result = future.result()
        if result is None or not result.success:
            self.resending = False
            self.get_logger().error("could not send the control program to the robot")
        self.switch(activate=[ARM_CONTROLLER])

    def switch(self, activate=(), deactivate=()):
        request = SwitchController.Request()
        request.activate_controllers = list(activate)
        request.deactivate_controllers = list(deactivate)
        request.strictness = SwitchController.Request.BEST_EFFORT
        self.switch_client.call_async(request)

    def on_program(self, msg):
        if msg.data == self.program_running:
            return
        self.program_running = msg.data
        if msg.data:
            self.warned = False
            self.resending = False
            self.get_logger().info("robot program running, the arm is ready")
        else:
            self.waiting_since = time.monotonic()
            self.get_logger().warn("robot program stopped, the arm will not move")
            # A lost connection kills the program while the robot stays ready
            if self.headless and not self.resending:
                self.retry = self.create_timer(1.0, self.retry_program)

    def retry_program(self):
        # Waits for a stop to show up in the robot or safety mode first
        self.retry.cancel()
        self.destroy_timer(self.retry)
        if self.ready() and not self.stopped and not self.program_running:
            self.recover()

    def on_remote(self, future):
        result = future.result()
        if result is None or not result.success:
            return
        was_local = self.remote is False
        self.remote = result.remote_control
        if not self.remote and not was_local:
            self.get_logger().warn(
                "robot in Local mode, switch it to Remote Control on the pendant"
            )
        elif self.remote and was_local:
            # The program never started in Local, nothing else would send it again
            self.get_logger().info("robot switched to Remote Control")
            self.recover()

    def check(self):
        stuck = self.robot_mode == RobotMode.RUNNING and not self.program_running
        if (
            stuck
            and self.headless
            and self.remote_client.service_is_ready()
        ):
            # Only e-Series robots answer, CB3 has no Local mode
            future = self.remote_client.call_async(IsInRemoteControl.Request())
            future.add_done_callback(self.on_remote)
        if not stuck or self.warned:
            return
        if time.monotonic() - self.waiting_since < PROGRAM_TIMEOUT:
            return
        self.warned = True
        if self.headless:
            self.get_logger().error(
                "the robot did not start the control program sent from here. "
                "e-Series robots must be in Remote Control mode. The robot has to "
                "reach this computer on ports 50001-50004, from a docker with its "
                "own network publish those ports and set UR_REVERSE_IP to this "
                "computer's address on the robot network"
            )
        else:
            self.get_logger().error(
                "the robot program is not running, start the program with the "
                "External Control node on the pendant and check its host IP"
            )


def main(args=None):
    rclpy.init(args=args)
    node = StatusNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
