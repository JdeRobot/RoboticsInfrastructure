#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import subprocess
import time
import random

class sausageSpawner(Node):

    def __init__(self):
        super().__init__('sausage_spawner')

        time.sleep(5)
        self.timer = self.create_timer(7.0, self.spawn_sausage)
        self.counter = 0

    def spawn_sausage(self):

        name = f"box_{self.counter}"

        x_random = random.uniform(-0.18, 0.18)

        cmd = [
            "ros2", "run", "ros_gz_sim", "create",
            "-name", name,
            "-x", str(x_random),
            "-y", "0.58",
            "-z", "0.8",
            "-file", "/home/ws/src/CustomRobots/conveyor_belt/sausage.sdf"
        ]

        subprocess.run(cmd)

        self.get_logger().info(f"Spawned {name}")
        self.counter += 1


def main():
    rclpy.init()
    node = sausageSpawner()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
