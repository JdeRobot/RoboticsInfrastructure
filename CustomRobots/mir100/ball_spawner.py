#!/usr/bin/env python3

import random
import subprocess
import threading

import rclpy
from rclpy.node import Node as RclpyNode
from rosgraph_msgs.msg import Clock
from std_msgs.msg import Empty

from gz.msgs10.pose_v_pb2 import Pose_V
from gz.transport13 import Node as GzNode, SubscribeOptions

WORLD = "default"

# Must match red_pipe/blue_pipe pose in mir100_warehouse.world.
PIPES = {
    "red": {"x": 3.84, "y": -2.5, "sdf": "/home/ws/src/CustomRobots/mir100/red_ball.sdf"},
    "blue": {"x": 3.84, "y": -6.0, "sdf": "/home/ws/src/CustomRobots/mir100/blue_ball.sdf"},
}
SPAWN_Z = 0.80  # just below the pipe opening

# Must match delivery_mat_1..4 pose in mir100_warehouse.world.
DELIVERY_MATS = {
    "delivery_mat_1": (1.2, -2.5),
    "delivery_mat_2": (1.2, -6.0),
    "delivery_mat_3": (-3.0, -4.5),
    "delivery_mat_4": (1.5, 2.0),
}

MARKER_SDF = {
    "red": "/home/ws/src/CustomRobots/mir100/red_mat_marker.sdf",
    "blue": "/home/ws/src/CustomRobots/mir100/blue_mat_marker.sdf",
}
MARKER_Z = 0.015  # above the mat, avoids z fighting

DELIVERY_RADIUS = 0.5  # meters from mat center


class BallSpawner(RclpyNode):
    def __init__(self):
        super().__init__("ball_spawner")

        self.counters = {"red": 0, "blue": 0}
        # Only one active ball and target mat per color.
        self.active_mat = {"red": None, "blue": None}
        self.active_ball = {"red": None, "blue": None}
        self._lock = threading.Lock()
        self._last_sim_time = 0.0

        self.create_subscription(
            Empty, "/mir100_warehouse/spawn_red_ball", self._make_callback("red"), 10
        )
        self.create_subscription(
            Empty, "/mir100_warehouse/spawn_blue_ball", self._make_callback("blue"), 10
        )
        self.create_subscription(Clock, "/clock", self._on_clock, 10)

        self._gz_node = GzNode()
        options = SubscribeOptions()
        options.msgs_per_sec = 20
        self._gz_node.subscribe(
            Pose_V,
            f"/world/{WORLD}/dynamic_pose/info",
            self._on_pose_update,
            options,
        )

        self.get_logger().info(
            "ball_spawner ready: publish Empty to "
            "/mir100_warehouse/spawn_{red,blue}_ball to drop a ball"
        )

    def _on_clock(self, msg):
        # Sim time going backward means the world got reset.
        t = msg.clock.sec + msg.clock.nanosec * 1e-9
        if t < self._last_sim_time:
            self._on_reset()
        self._last_sim_time = t

    def _on_reset(self):
        self.get_logger().info("world reset detected, clearing ball state")
        with self._lock:
            balls = list(self.active_ball.values())
            self.active_ball = {"red": None, "blue": None}
            self.active_mat = {"red": None, "blue": None}

        for ball in balls:
            if ball is not None:
                self._gz_remove(ball)
        self._gz_remove("red_delivery_marker")
        self._gz_remove("blue_delivery_marker")

    def _make_callback(self, color):
        def callback(_msg):
            self._spawn_ball(color)

        return callback

    def _spawn_ball(self, color):
        with self._lock:
            old_ball = self.active_ball[color]
        if old_ball is not None:
            self._gz_remove(old_ball)

        pipe = PIPES[color]
        name = f"{color}_ball_{self.counters[color]}"
        self.counters[color] += 1

        if not self._gz_create(pipe["sdf"], name, pipe["x"], pipe["y"], SPAWN_Z):
            return
        self.get_logger().info(f"spawned {name} at pipe ({pipe['x']}, {pipe['y']})")

        self._light_random_mat(color)
        with self._lock:
            self.active_ball[color] = name

    def _light_random_mat(self, color):
        # Never light the same mat for both colors at once.
        other = "blue" if color == "red" else "red"
        with self._lock:
            excluded = self.active_mat[other]
        choices = [m for m in DELIVERY_MATS if m != excluded]
        mat_name = random.choice(choices)

        marker_name = f"{color}_delivery_marker"
        self._gz_remove(marker_name)  # remove old marker for this color

        mx, my = DELIVERY_MATS[mat_name]
        self._gz_create(MARKER_SDF[color], marker_name, mx, my, MARKER_Z)

        with self._lock:
            self.active_mat[color] = mat_name
        self.get_logger().info(f"{color} delivery target: {mat_name}")

    def _on_pose_update(self, message):
        with self._lock:
            targets = [
                (color, self.active_ball[color], self.active_mat[color])
                for color in ("red", "blue")
                if self.active_ball[color] is not None
                and self.active_mat[color] is not None
            ]
        if not targets:
            return

        wanted_names = {ball for _, ball, _ in targets}
        positions = {}
        for pose in message.pose:
            if pose.name in wanted_names:
                positions[pose.name] = (pose.position.x, pose.position.y)

        for color, ball, mat in targets:
            pos = positions.get(ball)
            if pos is None:
                continue
            mx, my = DELIVERY_MATS[mat]
            dist = ((pos[0] - mx) ** 2 + (pos[1] - my) ** 2) ** 0.5
            if dist <= DELIVERY_RADIUS:
                self._deliver(color, ball)

    def _deliver(self, color, ball):
        with self._lock:
            if self.active_ball[color] != ball:
                return  # already delivered by a concurrent pose update
            self.active_ball[color] = None
            self.active_mat[color] = None

        self._gz_remove(ball)
        self._gz_remove(f"{color}_delivery_marker")
        self.get_logger().info(f"{ball} delivered, mat cleared")

    def _gz_create(self, sdf_path, name, x, y, z):
        cmd = [
            "ros2",
            "run",
            "ros_gz_sim",
            "create",
            "-name",
            name,
            "-x",
            str(x),
            "-y",
            str(y),
            "-z",
            str(z),
            "-file",
            sdf_path,
        ]
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            self.get_logger().error(f"failed to spawn {name}: {result.stderr.strip()}")
            return False
        return True

    def _gz_remove(self, name):
        cmd = [
            "gz",
            "service",
            "-s",
            f"/world/{WORLD}/remove",
            "--reqtype",
            "gz.msgs.Entity",
            "--reptype",
            "gz.msgs.Boolean",
            "--timeout",
            "2000",
            "--req",
            f"name: '{name}', type: MODEL",
        ]
        subprocess.run(cmd, check=False, capture_output=True, text=True)


def main():
    rclpy.init()
    node = BallSpawner()
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
