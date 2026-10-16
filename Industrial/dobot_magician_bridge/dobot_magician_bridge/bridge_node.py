#!/usr/bin/env python3
"""ROS2 driver that makes the real Dobot Magician look like the simulated one."""

import json
import math
import os
import threading
import time

import rclpy
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Bool

from dobot_magician_bridge.protocol import Dobot, find_port

ARM_JOINTS = ["joint_1", "joint_2", "joint_3", "joint_4"]

# The URDF parallelogram joints copy joint_2 and joint_3
MIMIC_JOINTS = {"joint_mimic_1": 1, "joint_mimic_2": 2}

# J2 and J3 go up before homing so the folded arm does not drag over the table
LIFT_J2 = 20.0
LIFT_J3 = 30.0

# Firmware joint speed limits in degrees per second
MIN_SPEED = 10.0
MAX_SPEED = 200.0

# Long trajectories are sampled down to this many queued points
MAX_WAYPOINTS = 10

# Simulated initial pose sent until the robot answers since MoveIt needs joint_states
DEFAULT_STATE = [0.0, 0.3, 0.3, 0.0]

# Keeps the homing across the relaunches RAM does when the code is stopped
HOMED_FILE = "/tmp/dobot_magician_homed.json"


def to_urdf(firmware):
    """The firmware measures J3 from the table and the URDF from the rear arm."""
    j1, j2, j3, j4 = firmware
    return [math.radians(j1), math.radians(j2), math.radians(j3 - j2), math.radians(j4)]


def to_firmware(urdf):
    q1, q2, q3, q4 = urdf
    return [math.degrees(q1), math.degrees(q2), math.degrees(q2 + q3), math.degrees(q4)]


def waypoints(start, points):
    """A straight joint space trajectory is one firmware move and anything else gets sampled."""
    end = points[-1]
    deltas = [b - a for a, b in zip(start, end)]
    lead = max(range(len(deltas)), key=lambda i: abs(deltas[i]))
    straight = True
    for q in points:
        s = (q[lead] - start[lead]) / deltas[lead] if deltas[lead] else 0.0
        if any(
            abs(q[i] - (start[i] + s * deltas[i])) > math.radians(1)
            for i in range(len(q))
        ):
            straight = False
            break
    if straight:
        return [end]
    step = math.ceil(len(points) / MAX_WAYPOINTS)
    sampled = points[step - 1 :: step]
    if sampled[-1] is not end:
        sampled.append(end)
    return sampled


class DobotMagicianBridge(Node):
    def __init__(self):
        super().__init__("dobot_magician_bridge")

        self.declare_parameter("port", "auto")
        self.declare_parameter("end_effector", "suction_cup")
        self.declare_parameter("rate", 20.0)
        # auto homes once per robot power on
        self.declare_parameter("homing", "auto")

        self.port = self.get_parameter("port").value
        self.end_effector = self.get_parameter("end_effector").value
        self.homing = self.get_parameter("homing").value

        self.dobot = None
        self.ready = threading.Event()
        self.current = None
        self.group = ReentrantCallbackGroup()

        self.joint_pub = self.create_publisher(JointState, "/joint_states", 10)
        self.create_timer(
            1.0 / self.get_parameter("rate").value,
            self.publish_joint_states,
            callback_group=self.group,
        )

        self.action_server = ActionServer(
            self,
            FollowJointTrajectory,
            "/joint_trajectory_controller/follow_joint_trajectory",
            execute_callback=self.execute,
            goal_callback=lambda goal: GoalResponse.ACCEPT,
            cancel_callback=lambda goal: CancelResponse.ACCEPT,
            callback_group=self.group,
        )

        if self.end_effector == "suction_cup":
            self.create_subscription(
                Bool,
                "/gripper_auto_attach",
                self.on_suction,
                10,
                callback_group=self.group,
            )

        threading.Thread(target=self.connect, daemon=True).start()

    def connect(self):
        warned = False
        while rclpy.ok() and self.dobot is None:
            path = find_port() if self.port == "auto" else self.port
            if path is None or not os.path.exists(path):
                if not warned:
                    self.get_logger().warn(
                        "Dobot Magician not found, plug its USB cable and power it on"
                    )
                    warned = True
                time.sleep(2.0)
                continue
            try:
                dobot = Dobot(path)
                if dobot.pose() is None:
                    dobot.close()
                    time.sleep(2.0)
                    continue
            except OSError as e:
                self.get_logger().warn(f"cannot open {path}: {e}")
                time.sleep(2.0)
                continue

            self.get_logger().info(f"Dobot Magician connected on {path}")
            self.dobot = dobot
            dobot.clear_alarms()
            dobot.start_queue()
            if self.needs_homing(dobot):
                self.home(dobot)
            self.ready.set()
            self.get_logger().info("Dobot Magician ready")

    def needs_homing(self, dobot):
        if self.homing in ("always", "never"):
            return self.homing == "always"
        device_time = dobot.device_time()
        if device_time is None or not os.path.exists(HOMED_FILE):
            return True
        with open(HOMED_FILE) as f:
            homed = json.load(f)
        # Same power on only if the robot's clock advanced as much as ours
        robot_elapsed = (device_time - homed["device_time"]) / 1000.0
        wall_elapsed = time.time() - homed["wall_time"]
        return abs(robot_elapsed - wall_elapsed) > 5.0

    def home(self, dobot):
        j1, j2, j3, j4 = dobot.pose()[4:]
        self.get_logger().info("raising the arm before homing, base untouched")
        dobot.set_speed(30.0, 30.0)
        dobot.wait_queue(dobot.move_joints(j1, LIFT_J2, LIFT_J3, j4), timeout=20.0)
        _, _, _, _, _, j2, j3, _ = dobot.pose()
        if abs(j2 - LIFT_J2) > 3 or abs(j3 - LIFT_J3) > 3:
            self.get_logger().error(
                "the arm did not go up, skipping homing, raise it by hand and relaunch"
            )
            return
        self.get_logger().info("homing, takes about 20 seconds")
        dobot.wait_queue(dobot.home(), timeout=60.0)
        with open(HOMED_FILE, "w") as f:
            json.dump({"device_time": dobot.device_time(), "wall_time": time.time()}, f)

    def publish_joint_states(self):
        dobot = self.dobot
        if dobot is None:
            self.publish(DEFAULT_STATE)
            return
        try:
            pose = dobot.pose()
        except OSError:
            self.get_logger().error("Dobot Magician disconnected")
            self.ready.clear()
            self.dobot = None
            self.current = None
            threading.Thread(target=self.connect, daemon=True).start()
            return
        if pose is not None:
            self.current = to_urdf(pose[4:])
            self.publish(self.current)

    def publish(self, state):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = ARM_JOINTS + list(MIMIC_JOINTS)
        msg.position = list(state) + [state[i] for i in MIMIC_JOINTS.values()]
        self.joint_pub.publish(msg)

    def on_suction(self, msg):
        if self.ready.is_set():
            self.dobot.suction_cup(msg.data)
            self.get_logger().info(f"suction cup {'on' if msg.data else 'off'}")

    def execute(self, goal_handle):
        result = FollowJointTrajectory.Result()
        trajectory = goal_handle.request.trajectory

        if not self.ready.wait(timeout=90.0) or self.current is None:
            goal_handle.abort()
            result.error_code = FollowJointTrajectory.Result.INVALID_GOAL
            result.error_string = "Dobot Magician not connected"
            return result

        try:
            order = [trajectory.joint_names.index(name) for name in ARM_JOINTS]
        except ValueError:
            goal_handle.abort()
            result.error_code = FollowJointTrajectory.Result.INVALID_JOINTS
            result.error_string = f"expected joints {ARM_JOINTS}"
            return result

        if not trajectory.points:
            goal_handle.succeed()
            return result

        start = list(self.current)
        points = [[p.positions[i] for i in order] for p in trajectory.points]
        targets = waypoints(start, points)

        last = trajectory.points[-1].time_from_start
        duration = max(last.sec + last.nanosec * 1e-9, 0.1)
        travel = max(
            sum(abs(b[i] - a[i]) for a, b in zip([start] + targets, targets))
            for i in range(len(ARM_JOINTS))
        )
        # A trapezoidal move takes about 1.5 times travel over top speed
        speed = min(max(1.5 * math.degrees(travel) / duration, MIN_SPEED), MAX_SPEED)

        dobot = self.dobot
        dobot.set_speed(speed, min(2 * speed, MAX_SPEED))
        index = None
        for target in targets:
            index = dobot.move_joints(*to_firmware(target))
            if index is None:
                break

        done = index is not None and dobot.wait_queue(
            index,
            timeout=3 * duration + 10.0,
            cancelled=lambda: goal_handle.is_cancel_requested,
        )

        if goal_handle.is_cancel_requested:
            dobot.force_stop()
            goal_handle.canceled()
            result.error_string = "cancelled"
            return result

        alarms = dobot.alarms()
        if not done or alarms:
            dobot.force_stop()
            dobot.clear_alarms()
            goal_handle.abort()
            result.error_code = FollowJointTrajectory.Result.PATH_TOLERANCE_VIOLATED
            result.error_string = (
                f"the robot raised alarms {alarms}, target out of its real range?"
                if alarms
                else "the robot did not reach the goal in time"
            )
            self.get_logger().error(result.error_string)
            return result

        goal_handle.succeed()
        result.error_code = FollowJointTrajectory.Result.SUCCESSFUL
        return result

    def stop(self):
        """Leave the robot still and the pump off when the launch goes down."""
        if self.dobot is not None:
            try:
                self.dobot.force_stop()
                self.dobot.suction_cup(False)
            except OSError:
                pass


def main(args=None):
    rclpy.init(args=args)
    node = DobotMagicianBridge()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.stop()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
