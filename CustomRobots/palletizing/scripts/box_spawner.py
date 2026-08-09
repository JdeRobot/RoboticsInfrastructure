#!/usr/bin/env python3
"""ROS integration for the palletizing feeder."""

import json
import os
import subprocess
import tempfile
from typing import Any

import rclpy
from ament_index_python.packages import get_package_share_directory
from feeder.box_model_generator import BoxModelGenerator
from feeder.gazebo_pose_tracker import GazeboPoseTracker
from feeder.state_machine import BoxFeederStateMachine
from feeder.task_loader import PalletizingTaskConfig
from rclpy.node import Node
from std_msgs.msg import Float64, String


class BoxSpawner(Node):
    def __init__(self):
        super().__init__("box_spawner")

        default_config = os.path.join(
            get_package_share_directory("custom_robots"),
            "config",
            "palletizing_task.yaml",
        )
        self.declare_parameter("task_config", default_config)
        config_path = str(self.get_parameter("task_config").value)

        self.task = PalletizingTaskConfig(config_path)
        self.state = BoxFeederStateMachine(self.task.box_count)
        self.conveyor = self.task.conveyor

        self.run_id = os.getpid() % 1000
        self.sdf_dir = tempfile.TemporaryDirectory(prefix=f"palletizing_boxes_{self.run_id}_")
        self.model_generator = BoxModelGenerator(self.sdf_dir.name)

        self.belt_speed = float(self.conveyor["belt_speed"])
        self.spawn_x = float(self.conveyor["spawn_x"])
        self.spawn_y = float(self.conveyor["spawn_y"])
        self.pickup_x = float(self.conveyor["pickup_x"])
        self.pickup_timeout = float(self.conveyor.get("pickup_timeout", 20.0))
        self.settle_delay = float(self.conveyor["settle_delay"])
        start_delay = float(self.conveyor["start_delay"])

        self.pose_tracker = GazeboPoseTracker()
        self.pickup_started_at = None
        self.pickup_world_position = None

        self.ready_timer = None
        self.event_timer = None

        self.speed_pub = self.create_publisher(Float64, "/conveyor/speed", 10)
        self.ready_pub = self.create_publisher(String, "/box_ready", 10)
        self.box_info_pub = self.create_publisher(String, "/box_info", 10)
        self.pallet_info_pub = self.create_publisher(String, "/pallet_info", 10)
        self.done_sub = self.create_subscription(String, "/box_done", self._on_box_done, 10)

        self.pallet_timer = self.create_timer(2.0, self._publish_pallet_info)
        self.start_timer = self.create_timer(start_delay, self._start)

        self._publish_pallet_info()
        self.get_logger().info(
            f"loaded {self.task.box_count} SKU boxes from {config_path}: {self.task.sequence}"
        )

    def _start(self) -> None:
        self.start_timer.cancel()
        self._spawn_next_box()

    def _spawn_next_box(self) -> None:
        if not self.state.has_next_box():
            self._finish()
            return

        box = self.task.box_at(self.state.index, self.run_id)
        sdf_path = self.model_generator.write_model(box)
        spawn_z = self.task.spawn_z(box)

        if not self._spawn_model(box, sdf_path, spawn_z):
            self._set_belt(0.0)
            return

        self.state.begin_spawn(box)
        self.pose_tracker.track(box["name"])
        self._start_belt_to_pickup(box["name"])

    def _spawn_model(self, box: dict[str, Any], sdf_path: str, spawn_z: float) -> bool:
        cmd = [
            "ros2", "run", "ros_gz_sim", "create",
            "-name", box["name"],
            "-x", str(self.spawn_x), "-y", str(self.spawn_y), "-z", str(spawn_z),
            "-R", "0", "-P", "0", "-Y", "0",
            "-file", sdf_path,
        ]
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            self.get_logger().error(
                f"failed to spawn {box['name']} ({box['sku']}): {result.stderr.strip()}"
            )
            return False

        self.get_logger().info(
            f"spawned {box['name']} sku={box['sku']} size={box['size']}"
        )
        return True

    def _start_belt_to_pickup(self, name: str) -> None:
        if abs(self.belt_speed) < 1e-6:
            self.get_logger().error("belt_speed is zero; cannot move box to pickup")
            self._set_belt(0.0)
            return

        self.pickup_started_at = self.get_clock().now()
        self.pickup_world_position = None
        self._set_belt(self.belt_speed)
        self.event_timer = self.create_timer(0.05, lambda: self._check_pickup_pose(name))

    def _check_pickup_pose(self, name: str) -> None:
        position = self.pose_tracker.position(name)
        if position is not None and position["x"] <= self.pickup_x:
            self._box_at_pickup(name, position)
            return

        if self.pickup_started_at is None:
            return

        elapsed = (self.get_clock().now() - self.pickup_started_at).nanoseconds / 1e9
        if elapsed >= self.pickup_timeout:
            self._cancel_event_timer()
            self._set_belt(0.0)
            self.pose_tracker.clear()
            self.get_logger().error(
                f"{name} did not reach pickup_x={self.pickup_x:.3f} within "
                f"{self.pickup_timeout:.1f}s; last pose={position}"
            )

    def _box_at_pickup(self, name: str, position: dict[str, float]) -> None:
        self._cancel_event_timer()
        self._set_belt(0.0)
        self.pickup_world_position = position
        self.state.reached_pickup()
        self.get_logger().info(
            f"{name} reached pickup point at world "
            f"x={position['x']:.3f}, y={position['y']:.3f}, z={position['z']:.3f}"
        )
        self.event_timer = self.create_timer(
            self.settle_delay,
            lambda: self._announce_ready(name),
        )

    def _announce_ready(self, name: str) -> None:
        self._cancel_event_timer()
        settled_position = self.pose_tracker.position(name)
        if settled_position is not None:
            self.pickup_world_position = settled_position
        self.pose_tracker.clear()

        self.state.ready()
        self.ready_timer = self.create_timer(1.0, self._publish_ready)
        self._publish_ready()
        self.get_logger().info(
            f"{name} ready for pickup at world pose {self.pickup_world_position} "
            "— waiting for /box_done"
        )

    def _publish_ready(self) -> None:
        box = self.state.pending_box
        if box is None:
            return
        if self.pickup_world_position is None:
            self.get_logger().error(f"missing observed pickup pose for {box['name']}")
            return

        self.ready_pub.publish(String(data=box["name"]))
        info = self.task.box_info(box, self.pickup_world_position)
        self.box_info_pub.publish(String(data=json.dumps(info)))

    def _publish_pallet_info(self) -> None:
        self.pallet_info_pub.publish(String(data=json.dumps(self.task.pallet_info())))

    def _on_box_done(self, msg: String) -> None:
        expected = self.state.expected_name()
        if not self.state.accept_done(msg.data):
            self.get_logger().warn(
                f"ignoring /box_done '{msg.data}' (waiting on '{expected}')"
            )
            return

        self._cancel_ready_timer()
        self.pickup_world_position = None
        self.pickup_started_at = None
        self.pose_tracker.clear()
        self.get_logger().info(f"{msg.data} picked by robot")
        self._spawn_next_box()

    def _set_belt(self, speed: float) -> None:
        self.speed_pub.publish(Float64(data=float(speed)))
        self.get_logger().info(f"belt speed → {speed:.2f} m/s")

    def _finish(self) -> None:
        self._set_belt(0.0)
        self.get_logger().info(f"all {self.task.box_count} boxes fed — task complete")

    def _cancel_event_timer(self) -> None:
        if self.event_timer is not None:
            self.event_timer.cancel()
            self.event_timer = None

    def _cancel_ready_timer(self) -> None:
        if self.ready_timer is not None:
            self.ready_timer.cancel()
            self.ready_timer = None

    def destroy_node(self) -> None:
        self._cancel_event_timer()
        self._cancel_ready_timer()
        self.pose_tracker.clear()
        self.sdf_dir.cleanup()
        super().destroy_node()


def main() -> None:
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
