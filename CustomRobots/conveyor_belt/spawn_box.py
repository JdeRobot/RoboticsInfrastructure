#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import subprocess
import time

class BoxSpawner(Node):

    def __init__(self):
        super().__init__('box_spawner')

        time.sleep(5)
        self.timer = self.create_timer(3.0, self.spawn_box)
        self.counter = 0

    def spawn_box(self):

        name = f"box_{self.counter}"

        cmd = [
            "ros2", "run", "ros_gz_sim", "create",
            "-name", name,
            "-x", "0.0",
            "-y", "0.0",
            "-z", "0.75",
            "-file", "/home/ws/src/CustomRobots/conveyor_belt/box.sdf"
        ]

        subprocess.run(cmd)

        self.get_logger().info(f"Spawned {name}")
        self.counter += 1


def main():
    rclpy.init()
    node = BoxSpawner()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()