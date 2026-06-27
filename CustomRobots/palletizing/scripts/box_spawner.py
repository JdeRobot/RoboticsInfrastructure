#!/usr/bin/env python3
"""Palletizing conveyor feeder.

Feeds a fixed number of boxes (num_boxes), one at a time, and stacks them into
a real rows x cols x layers grid on the pallet table. This is the palletizing
task: a finite supply that must end up in an ordered pattern — not an infinite
stream.

Lifecycle per box:
  1. Spawn at belt feed end (fixed X, Y = spawn_y).
  2. Belt runs at belt_speed m/s; box rides straight to centre (Y = center_y).
  3. Belt stops; the box name is published on /box_ready. The robot (the
     student/reference exercise code) picks the box and stacks it on the pallet,
     then signals completion by publishing the box name on /box_done.
  4. On /box_done the belt restarts and the next box is spawned — until
     num_boxes have been fed, then the belt stops and the feeder idles.

This node no longer places boxes itself: picking and palletizing is the robot's
job. The feeder only meters one box at a time and waits for the robot before
releasing the next, so boxes never pile up at the pickup point.
"""

import os
import subprocess

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64, String
from ament_index_python.packages import get_package_share_directory


class BoxSpawner(Node):
    def __init__(self):
        super().__init__("box_spawner")

        default_file = ""
        try:
            share = get_package_share_directory("custom_robots")
            default_file = f"{share}/models/palletizing_box/model.sdf"
        except Exception as exc:
            self.get_logger().warn(f"could not resolve custom_robots share: {exc}")

        self.declare_parameter("sdf_file", default_file)
        self.declare_parameter("belt_speed", 0.12)    # m/s — slow enough to stop cleanly
        self.declare_parameter("spawn_x", 0.6)        # belt centre in world X
        self.declare_parameter("spawn_y", -0.9)       # feed end in world Y
        self.declare_parameter("spawn_z", 1.13)       # belt surface ~1.00 m + box half-height 0.10 m + clearance
        self.declare_parameter("center_y", -0.15)     # stop before pickup end so coasting box doesn't fall off
        self.declare_parameter("start_delay", 5.0)    # wait for gz to be ready
        self.declare_parameter("settle_delay", 0.3)   # let physics settle the box before signalling
        # Total boxes to feed. Placement (grid pattern) is the robot's job now.
        self.declare_parameter("num_boxes", 8)

        self.sdf_file = self.get_parameter("sdf_file").value
        self.num_boxes = int(self.get_parameter("num_boxes").value)
        self.counter = 0
        self._active_timer = None
        self._pending_box = None      # box currently awaiting /box_done
        # Unique prefix per process so box names never conflict with leftover
        # entities from a previous (not-fully-cleaned) gz sim session.
        self._run_id = os.getpid() % 1000

        self._speed_pub = self.create_publisher(Float64, "/conveyor/speed", 10)
        # Handshake with the robot: announce a box is at the pickup point, then
        # wait for the robot to report it has been palletized before feeding next.
        self._ready_pub = self.create_publisher(String, "/box_ready", 10)
        self._done_sub = self.create_subscription(
            String, "/box_done", self._on_box_done, 10
        )

        delay = float(self.get_parameter("start_delay").value)
        self._init_timer = self.create_timer(delay, self._start)

    # ------------------------------------------------------------------

    def _start(self):
        self._init_timer.cancel()
        self._set_belt(float(self.get_parameter("belt_speed").value))
        self._spawn_next()

    def _set_belt(self, speed: float):
        msg = Float64()
        msg.data = speed
        self._speed_pub.publish(msg)
        self.get_logger().info(f"belt speed → {speed:.2f} m/s")

    def _spawn_next(self):
        name = f"box_{self._run_id}_{self.counter}"
        x = float(self.get_parameter("spawn_x").value)
        y = float(self.get_parameter("spawn_y").value)
        z = float(self.get_parameter("spawn_z").value)

        cmd = [
            "ros2", "run", "ros_gz_sim", "create",
            "-name", name,
            "-x", str(x), "-y", str(y), "-z", str(z),
            "-R", "0", "-P", "0", "-Y", "0",
            "-file", self.sdf_file,
        ]
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            self.get_logger().error(
                f"spawn {name} failed (rc={result.returncode}): {result.stderr.strip()}"
            )
            return

        self.get_logger().info(f"spawned {name} at ({x:.2f}, {y:.2f}, {z:.2f})")

        # Time for box to travel from spawn_y to center_y at belt_speed.
        belt_speed = float(self.get_parameter("belt_speed").value)
        travel = abs(float(self.get_parameter("center_y").value) - y) / belt_speed
        self.get_logger().info(f"{name}: belt stops in {travel:.1f} s")
        self._active_timer = self.create_timer(travel, lambda: self._box_at_centre(name))
        self.counter += 1

    def _box_at_centre(self, name: str):
        if self._active_timer:
            self._active_timer.cancel()
            self._active_timer = None

        self.get_logger().info(f"{name} reached centre — stopping belt")
        self._set_belt(0.0)

        # Give the physics engine a moment to settle the box before telling the
        # robot to pick it (a box still drifting makes the grasp pose stale).
        settle = float(self.get_parameter("settle_delay").value)
        self._active_timer = self.create_timer(settle, lambda: self._announce_ready(name))

    def _announce_ready(self, name: str):
        if self._active_timer:
            self._active_timer.cancel()
            self._active_timer = None

        # Hand the box off to the robot and wait for /box_done. Publish continuously
        # so a late-started solution.py doesn't miss the message!
        self._pending_box = name
        self._active_timer = self.create_timer(1.0, lambda: self._ready_pub.publish(String(data=self._pending_box)))
        self._ready_pub.publish(String(data=name))
        self.get_logger().info(f"{name} ready for pickup — waiting for robot")

    def _on_box_done(self, msg: String):
        if self._active_timer:
            self._active_timer.cancel()
            self._active_timer = None

        # Ignore stray/duplicate acks not matching the box we're waiting on.
        if msg.data != self._pending_box:
            self.get_logger().warn(
                f"ignoring /box_done '{msg.data}' (waiting on '{self._pending_box}')"
            )
            return

        self.get_logger().info(f"{msg.data} palletized by robot")
        self._pending_box = None
        self._resume()

    def _resume(self):
        # Finite supply: stop once every box has been fed and palletized.
        if self.counter >= self.num_boxes:
            self._set_belt(0.0)
            self.get_logger().info(
                f"all {self.num_boxes} boxes palletized — task complete, feeder idle"
            )
            return

        self._set_belt(float(self.get_parameter("belt_speed").value))
        self._spawn_next()


def main():
    rclpy.init()
    node = BoxSpawner()
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
