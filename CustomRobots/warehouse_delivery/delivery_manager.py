#!/usr/bin/env python3

import os
import random
import subprocess
import threading
import time

import rclpy
from rclpy.node import Node as RclpyNode
from rclpy.qos import QoSProfile, DurabilityPolicy
from rosgraph_msgs.msg import Clock
from std_msgs.msg import Bool, Empty, Int32

from gz.msgs10.pose_v_pb2 import Pose_V
from gz.transport13 import Node as GzNode, SubscribeOptions

WORLD = "default"
MODELS_DIR = os.path.dirname(os.path.abspath(__file__))

# Must match the dispensers and delivery stations in warehouse_delivery.world
CUP_X = 6.671
DISPENSERS = {"red": (CUP_X, -2.0), "blue": (CUP_X, -6.0)}
SPAWN_Z = 0.26
STATIONS = {
    1: (-3.6, 6.0),
    2: (-3.6, -3.5),
    3: (1.0, -8.6),
    4: (1.0, 5.5),
    5: (4.0, 0.8),
}
MARKER_Z = 0.008

# A delivered ball lies inside the box walls below their top
BOX_INNER_HALF = 0.095
BOX_TOP_Z = 0.072
# and has been released and still for this long
SETTLE_TIME = 1.0
SETTLE_MOTION = 0.003
GREEN_FLASH_TIME = 2.0


class DeliveryManager(RclpyNode):
    def __init__(self):
        super().__init__("delivery_manager")

        self.counters = {"red": 0, "blue": 0}
        self.scores = {"red": 0, "blue": 0}
        # One ball waiting for delivery and one target station per color
        self.active_ball = {"red": None, "blue": None}
        self.target = {"red": 0, "blue": 0}
        self.all_balls = []
        self.released = True
        self.settle = {}
        self.last_pose = {}
        self._lock = threading.Lock()
        # Spawns and resets run one at a time so they never interleave
        self._ops = threading.Lock()
        self._last_sim_time = 0.0

        self.create_subscription(
            Empty, "/warehouse_delivery/spawn_red_ball", self._spawn_cb("red"), 10
        )
        self.create_subscription(
            Empty, "/warehouse_delivery/spawn_blue_ball", self._spawn_cb("blue"), 10
        )
        self.create_subscription(Bool, "/gripper_auto_attach", self._on_gripper, 10)
        self.create_subscription(Clock, "/clock", self._on_clock, 10)

        # Latched so the HAL and the GUI get the current value when they start
        latched = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.target_pub = {
            c: self.create_publisher(Int32, f"/warehouse_delivery/{c}_target", latched)
            for c in ("red", "blue")
        }
        self.score_pub = {
            c: self.create_publisher(Int32, f"/warehouse_delivery/{c}_score", latched)
            for c in ("red", "blue")
        }
        for c in ("red", "blue"):
            self.target_pub[c].publish(Int32(data=0))
            self.score_pub[c].publish(Int32(data=0))

        self._gz_node = GzNode()
        options = SubscribeOptions()
        options.msgs_per_sec = 20
        self._gz_node.subscribe(
            Pose_V, f"/world/{WORLD}/dynamic_pose/info", self._on_poses, options
        )

        # Checked on a timer because a still ball may stop getting pose updates
        self.create_timer(0.2, self._check_deliveries)

        self.get_logger().info("delivery_manager ready")

    def _spawn_cb(self, color):
        def callback(_msg):
            threading.Thread(
                target=self._spawn_ball, args=(color,), daemon=True
            ).start()

        return callback

    def _on_gripper(self, msg):
        # The HAL closes the gripper and arms auto attach together
        self.released = not msg.data

    def _on_clock(self, msg):
        # Sim time going backwards means the world was reset
        t = msg.clock.sec + msg.clock.nanosec * 1e-9
        if t < self._last_sim_time:
            threading.Thread(target=self._on_reset, daemon=True).start()
        self._last_sim_time = t

    def _on_reset(self):
        with self._ops:
            self._clear_all()

    def _clear_all(self):
        self.get_logger().info("world reset, clearing balls and scores")
        with self._lock:
            balls = list(self.all_balls)
            self.all_balls = []
            self.active_ball = {"red": None, "blue": None}
            self.target = {"red": 0, "blue": 0}
            self.scores = {"red": 0, "blue": 0}
            self.settle = {}
            self.last_pose = {}
        for ball in balls:
            self._gz_remove(ball)
        for name in ("red_marker", "blue_marker", "green_marker"):
            self._gz_remove(name)
        for c in ("red", "blue"):
            self.target_pub[c].publish(Int32(data=0))
            self.score_pub[c].publish(Int32(data=0))

    def _spawn_ball(self, color):
        with self._ops:
            self._spawn_ball_locked(color)

    def _spawn_ball_locked(self, color):
        with self._lock:
            old_ball = self.active_ball[color]
            self.active_ball[color] = None
        # Only one ball per color waits for delivery at a time
        if old_ball is not None:
            self._gz_remove(old_ball)

        name = f"{color}_ball_{self.counters[color]}"
        self.counters[color] += 1
        x, y = DISPENSERS[color]
        if not self._gz_create(f"{color}_ball.sdf", name, x, y, SPAWN_Z):
            return

        station = self._pick_station(color)
        with self._lock:
            self.all_balls.append(name)
            self.active_ball[color] = name
            self.target[color] = station
            self.settle.pop(name, None)
        self.target_pub[color].publish(Int32(data=station))
        self.get_logger().info(f"{name} dropped, deliver it to station {station}")

    def _pick_station(self, color):
        other = "blue" if color == "red" else "red"
        with self._lock:
            excluded = {self.target[other], self.target[color]}
        station = random.choice([s for s in STATIONS if s not in excluded])
        self._gz_remove(f"{color}_marker")
        sx, sy = STATIONS[station]
        self._gz_create(f"{color}_marker.sdf", f"{color}_marker", sx, sy, MARKER_Z)
        return station

    def _on_poses(self, message):
        with self._lock:
            watched = {b for b in self.active_ball.values() if b is not None}
            for pose in message.pose:
                if pose.name in watched:
                    p = pose.position
                    self.last_pose[pose.name] = (p.x, p.y, p.z)

    def _check_deliveries(self):
        now = time.monotonic()
        with self._lock:
            balls = [
                (c, b, self.last_pose.get(b))
                for c, b in self.active_ball.items()
                if b is not None
            ]
        for color, ball, p in balls:
            if p is not None and self._settled_in_box(ball, color, p, now):
                self._deliver(color, ball)

    def _settled_in_box(self, name, color, p, now):
        station = self.target[color]
        if station == 0:
            return False
        sx, sy = STATIONS[station]
        inside = (
            abs(p[0] - sx) < BOX_INNER_HALF
            and abs(p[1] - sy) < BOX_INNER_HALF
            and p[2] < BOX_TOP_Z
        )
        if not inside or not self.released:
            self.settle.pop(name, None)
            return False

        start = self.settle.get(name)
        if (
            start is None
            or max(abs(a - b) for a, b in zip(p, start[1])) > SETTLE_MOTION
        ):
            self.settle[name] = (now, p)
            return False
        return now - start[0] >= SETTLE_TIME

    def _deliver(self, color, ball):
        with self._lock:
            if self.active_ball[color] != ball:
                return
            station = self.target[color]
            self.active_ball[color] = None
            self.target[color] = 0
            self.scores[color] += 1
            score = self.scores[color]
        self.target_pub[color].publish(Int32(data=0))
        self.score_pub[color].publish(Int32(data=score))
        self.get_logger().info(
            f"{ball} delivered to station {station}, {color} score {score}"
        )
        self._gz_remove(f"{color}_marker")
        # The ball stays in the box and the station flashes green
        threading.Thread(target=self._flash_green, args=(station,), daemon=True).start()

    def _flash_green(self, station):
        sx, sy = STATIONS[station]
        self._gz_create("green_marker.sdf", "green_marker", sx, sy, MARKER_Z)
        time.sleep(GREEN_FLASH_TIME)
        self._gz_remove("green_marker")

    def _gz_create(self, sdf_file, name, x, y, z):
        sdf = os.path.join(MODELS_DIR, sdf_file)
        req = (
            f"sdf_filename: '{sdf}', name: '{name}', "
            f"pose: {{position: {{x: {x}, y: {y}, z: {z}}}}}"
        )
        ok = self._gz_service("create", "gz.msgs.EntityFactory", req)
        if not ok:
            self.get_logger().error(f"failed to spawn {name}")
        return ok

    def _gz_remove(self, name):
        self._gz_service("remove", "gz.msgs.Entity", f"name: '{name}', type: MODEL")

    def _gz_service(self, service, req_type, req):
        # Timeouts so a call made during a world reset never blocks the manager
        cmd = [
            "gz",
            "service",
            "-s",
            f"/world/{WORLD}/{service}",
            "--reqtype",
            req_type,
            "--reptype",
            "gz.msgs.Boolean",
            "--timeout",
            "3000",
            "--req",
            req,
        ]
        try:
            result = subprocess.run(
                cmd, check=False, capture_output=True, text=True, timeout=6
            )
        except subprocess.TimeoutExpired:
            return False
        return result.returncode == 0 and "data: true" in result.stdout


def main():
    rclpy.init()
    node = DeliveryManager()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
