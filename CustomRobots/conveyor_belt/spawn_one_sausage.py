#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

import subprocess
import time
import random
import math
import json

from std_msgs.msg import String, Float64, Bool

from rclpy.qos import (
    QoSProfile,
    ReliabilityPolicy,
    DurabilityPolicy
)


class sausageSpawner(Node):

    def __init__(self):
        super().__init__("sausage_spawner")

        self.BELT_SPEED = -0.07
        self.MIN_X = -0.1
        self.MAX_X = 0.1
        self.SPAWN_Y = 0.58
        self.SPAWN_Z = 0.76
        self.SPAWN_INTERVAL = 50.0

        self.SAUSAGE_SDF = (
            "/home/ws/src/CustomRobots/"
            "conveyor_belt/sausage.sdf"
        )

        self.counter = 0
        self.sausages = {}
        self.last_spawn_time = 0.0
        self.belt_started = False
        self.sausage_contact = False

        self.graspable_pub = self.create_publisher(
            String,
            "/graspable_objects",
            10
        )

        sausage_info_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL
        )

        self.sausage_info_pub = self.create_publisher(
            String,
            "/sausage_info",
            sausage_info_qos
        )

        self.speed_pub = self.create_publisher(
            Float64,
            "/conveyor/speed",
            10
        )

        self.contact_sub = self.create_subscription(
            Bool,
            "/sausage_contact",
            self.contact_callback,
            10
        )

        self.belt_timer = self.create_timer(
            0.01,
            self.update_belt
        )

        self.spawn_timer = self.create_timer(
            0.1,
            self.update_spawn
        )

        self.get_logger().info(
            "Waiting 5 seconds for Gazebo..."
        )

        time.sleep(5)

        self.publish_graspable_objects()

        self.get_logger().info(
            "Waiting 20 seconds before spawning the first sausage..."
        )

        time.sleep(20)

        self.spawn_sausage()
        self.last_spawn_time = time.monotonic()
        self.start_belt()

    def publish_graspable_objects(self):

        msg = String()

        msg.data = ",".join(
            [
                f"box_{i}"
                for i in range(self.counter)
            ]
        )

        self.graspable_pub.publish(msg)

        self.get_logger().info(
            f"Graspable objects -> {msg.data}"
        )

    def publish_sausage_info(
        self,
        name,
        x,
        y,
        yaw
    ):

        msg = String()

        msg.data = json.dumps({
            "name": name,
            "x": x,
            "y": y,
            "yaw": yaw
        })

        self.sausage_info_pub.publish(msg)

        self.get_logger().info(
            f"Sausage info -> {msg.data}"
        )

    def set_belt(self, speed):

        msg = Float64()

        msg.data = float(speed)

        self.speed_pub.publish(msg)

    def start_belt(self):

        if self.belt_started:
            return

        self.belt_started = True

        self.get_logger().info(
            f"Starting conveyor at "
            f"{self.BELT_SPEED:.2f} m/s"
        )

    def update_belt(self):

        if not self.belt_started:
            return

        if self.sausage_contact:
            self.set_belt(0.0)
        else:
            self.set_belt(self.BELT_SPEED)

    def update_spawn(self):

        if not self.belt_started:
            return

        now = time.monotonic()
        elapsed = now - self.last_spawn_time

        if elapsed >= self.SPAWN_INTERVAL:
            self.spawn_sausage()
            self.last_spawn_time = now

    def spawn_sausage(self):
        name = f"box_{self.counter}"

        x = random.uniform(
            self.MIN_X,
            self.MAX_X
        )

        y = self.SPAWN_Y
        yaw_deg = random.uniform(-150.0, -120.0)
        yaw = math.radians(yaw_deg)

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
            str(self.SPAWN_Z),
            "-R",
            "0",
            "-P",
            "0",
            "-Y",
            str(yaw),
            "-file",
            self.SAUSAGE_SDF,
        ]

        self.get_logger().info(
            f"Spawning {name}: "
            f"x={x:.3f}, "
            f"y={y:.3f}, "
            f"z={self.SPAWN_Z:.3f}, "
            f"yaw={yaw:.3f}"
        )

        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            self.get_logger().error(
                f"Failed to spawn {name}: "
                f"{result.stderr.strip()}"
            )
            return

        self.sausages[name] = {
            "x": x,
            "y": y,
            "z": self.SPAWN_Z,
            "yaw": yaw
        }

        self.counter += 1

        self.publish_sausage_info(
            name,
            x,
            y,
            yaw
        )

        self.publish_graspable_objects()

        self.get_logger().info(
            f"Spawned {name} successfully. "
            f"Total sausages: {self.counter}"
        )

    def destroy_node(self):
        if hasattr(self, "speed_pub"):
            msg = Float64()
            msg.data = 0.0
            self.speed_pub.publish(msg)

        super().destroy_node()

    def contact_callback(self, msg):
        if self.sausage_contact == msg.data:
            return

        self.sausage_contact = msg.data

        if self.sausage_contact:
            self.get_logger().info(
                "Sausage contact detected. "
                "Stopping the conveyor belt."
            )
        else:
            self.get_logger().info(
                "Contact deactivated. "
                "Resuming the conveyor belt."
            )


def main():
    rclpy.init()
    node = sausageSpawner()
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