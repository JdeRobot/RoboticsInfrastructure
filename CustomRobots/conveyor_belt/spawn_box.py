#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import subprocess
import time

class BoxSpawner(Node):

    def __init__(self):
        super().__init__('box_spawner')

        time.sleep(3)  # esperar a Gazebo
        self.timer = self.create_timer(3.0, self.spawn_box)
        self.counter = 0

    def spawn_box(self):

        name = f"box_{self.counter}"

        cmd = [
            "ros2", "run", "ros_gz_sim", "create",
            "-name", name,
            "-x", "0.0",
            "-y", "0.0",
            "-z", "0.8",
            "-file", "/home/ws/src/CustomRobots/conveyor_belt/box.sdf"
        ]

        self.get_logger().info(f"Running: {' '.join(cmd)}")

        try:
            subprocess.run(cmd, check=True)
            self.get_logger().info(f"Spawned {name}")
        except Exception as e:
            self.get_logger().error(str(e))

        self.counter += 1


def main():
    rclpy.init()
    node = BoxSpawner()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()