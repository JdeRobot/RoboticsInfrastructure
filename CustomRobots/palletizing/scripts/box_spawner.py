#!/usr/bin/env python3
"""Palletizing conveyor feeder.

Feeds a fixed number of boxes (num_boxes), one at a time, and stacks them into
a real rows x cols x layers grid on the pallet table. This is the palletizing
task: a finite supply that must end up in an ordered pattern — not an infinite
stream.

Lifecycle per box:
  1. Spawn at belt feed end (fixed X, Y = spawn_y).
  2. Belt runs at belt_speed m/s; box rides straight to centre (Y = center_y).
  3. Belt stops; box is teleported to its grid cell on the pallet table (a dev
     placeholder for the eventual robot pick-and-place action).
  4. After a short pause, belt restarts and the next box is spawned — until
     num_boxes have been placed, then the belt stops and the feeder idles.

The grid cell for box i is computed in _place_on_table(): boxes fill layer by
layer, and within a layer row by row, column by column.
"""

import math
import os
import subprocess

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
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
        self.declare_parameter("restart_delay", 2.0)  # pause after placing before next box

        # --- Pallet grid (target pattern) -------------------------------------
        # Box is 0.40 (long) x 0.30 x 0.20 (tall). Placed yawed 1.57 rad so the
        # 0.40 long axis runs along the table's long axis (world Y) and the 0.30
        # axis along world X. 2 cols x 2 rows x 2 layers = 8 boxes.
        self.declare_parameter("num_boxes", 8)
        self.declare_parameter("grid_cols", 2)        # along world X (0.30 box axis)
        self.declare_parameter("grid_rows", 2)        # along world Y (0.40 box axis)
        self.declare_parameter("grid_layers", 2)      # stacked in Z
        self.declare_parameter("grid_origin_x", -0.70)  # near corner of grid, world X (cols at -0.70,-0.37 fit table X -1.0..-0.2)
        self.declare_parameter("grid_origin_y", -0.22)  # near corner of grid, world Y (rows centred about table Y=0)
        self.declare_parameter("grid_base_z", 0.86)   # table surface 0.76 + box half-height 0.10
        self.declare_parameter("pitch_x", 0.33)       # col spacing: 0.30 box + 0.03 gap
        self.declare_parameter("pitch_y", 0.43)       # row spacing: 0.40 box + 0.03 gap
        self.declare_parameter("pitch_z", 0.20)       # layer spacing == box height
        self.declare_parameter("place_yaw", 1.57)     # long axis along world Y

        self.sdf_file = self.get_parameter("sdf_file").value
        self.num_boxes = int(self.get_parameter("num_boxes").value)
        self.counter = 0
        self._active_timer = None
        # Unique prefix per process so box names never conflict with leftover
        # entities from a previous (not-fully-cleaned) gz sim session.
        self._run_id = os.getpid() % 1000

        self._speed_pub = self.create_publisher(Float64, "/conveyor/speed", 10)

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

        # Give the physics engine 0.3 s to settle the box before teleporting.
        # Without this, set_pose_vector occasionally can't find the entity by name.
        self._active_timer = self.create_timer(0.3, lambda: self._teleport_and_resume(name))

    def _teleport_and_resume(self, name: str):
        if self._active_timer:
            self._active_timer.cancel()
            self._active_timer = None

        self._place_on_table(name)
        restart = float(self.get_parameter("restart_delay").value)
        self._active_timer = self.create_timer(restart, self._resume)

    def _place_on_table(self, name: str):
        """Teleport box to its grid cell on the pallet table.

        Dev stand-in for the eventual robot pick-and-place. Boxes fill the grid
        layer by layer (bottom first), and within a layer row by row, column by
        column. Box i (0-based) maps to (layer, row, col) by integer division.
        """
        cols = int(self.get_parameter("grid_cols").value)
        rows = int(self.get_parameter("grid_rows").value)
        per_layer = cols * rows

        idx = self.counter - 1
        layer = idx // per_layer
        within = idx % per_layer
        row = within // cols
        col = within % cols

        tx = float(self.get_parameter("grid_origin_x").value) + col * float(self.get_parameter("pitch_x").value)
        ty = float(self.get_parameter("grid_origin_y").value) + row * float(self.get_parameter("pitch_y").value)
        tz = float(self.get_parameter("grid_base_z").value) + layer * float(self.get_parameter("pitch_z").value)

        # Yaw the box so its long axis aligns with the grid (rotation about Z).
        yaw = float(self.get_parameter("place_yaw").value)
        qz = math.sin(yaw / 2.0)
        qw = math.cos(yaw / 2.0)

        req = (
            f'pose: [{{name: "{name}", '
            f'position: {{x: {tx}, y: {ty}, z: {tz}}}, '
            f'orientation: {{x: 0, y: 0, z: {qz}, w: {qw}}}}}]'
        )
        cmd = [
            "gz", "service",
            "-s", "/world/default/set_pose_vector",
            "--reqtype", "gz.msgs.Pose_V",
            "--reptype", "gz.msgs.Boolean",
            "--timeout", "2000",
            "--req", req,
        ]
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if result.returncode == 0:
            self.get_logger().info(
                f"placed {name} at grid cell L{layer} R{row} C{col} "
                f"-> ({tx:.2f}, {ty:.2f}, {tz:.2f})"
            )
        else:
            self.get_logger().warn(f"place {name} failed: {result.stderr.strip()}")

    def _resume(self):
        if self._active_timer:
            self._active_timer.cancel()
            self._active_timer = None

        # Finite supply: stop once the whole grid has been filled.
        if self.counter >= self.num_boxes:
            self._set_belt(0.0)
            self.get_logger().info(
                f"all {self.num_boxes} boxes placed — palletizing complete, feeder idle"
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
