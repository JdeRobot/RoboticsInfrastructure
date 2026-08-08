#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import subprocess
import time
import random
import math
from std_msgs.msg import String

class sausageSpawner(Node):

    def __init__(self):
        super().__init__("sausage_spawner")

        time.sleep(5)
        #self.timer = self.create_timer(30.0, self.spawn_sausage)
        self.counter = 0
        self.graspable_pub = self.create_publisher(
            String,
            "/graspable_objects",
            10
        )
        self.publish_graspable_objects()
        time.sleep(20)
        self.spawn_all_sausages()

    def publish_graspable_objects(self):

        msg = String()

        msg.data = ",".join(
            [f"box_{i}" for i in range(self.counter)]
        )

        self.graspable_pub.publish(msg)

    def spawn_sausage(self):

        if self.counter >= 4:
            return

        name = f"box_{self.counter}"

        x_random = random.uniform(-0.18, 0.18)
        yaw = random.uniform(-2 * math.pi, 2 * math.pi)

        cmd = [
            "ros2",
            "run",
            "ros_gz_sim",
            "create",
            "-name",
            name,
            "-x",
            str(x_random),
            "-y",
            "0.58",
            "-z",
            "0.78",
            "-R",
            "0",
            "-P",
            "0",
            "-Y",
            str(yaw),
            "-file",
            "/home/ws/src/CustomRobots/conveyor_belt/sausage.sdf",
        ]

        subprocess.run(cmd)

        self.get_logger().info(f"Spawned {name}")
        time.sleep(0.2)
        self.counter += 1
        self.publish_graspable_objects()
        self.get_logger().info(f"Spawned {name}")

    def spawn_all_sausages(self):
        NUM_SAUSAGES = 4

        MIN_X = -0.18
        MAX_X = 0.18

        MIN_DISTANCE = 0.08      # 8 cm entre salchichas

        positions = []

        while len(positions) < NUM_SAUSAGES:

            x = random.uniform(MIN_X, MAX_X)

            valid = True

            for p in positions:
                if abs(x - p) < MIN_DISTANCE:
                    valid = False
                    break

            if valid:
                positions.append(x)

        positions.sort()

        for x in positions:

            name = f"box_{self.counter}"

            yaw = random.uniform(-math.pi, math.pi)

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
                "0.58",
                "-z",
                "0.78",
                "-R",
                "0",
                "-P",
                "0",
                "-Y",
                str(yaw),
                "-file",
                "/home/ws/src/CustomRobots/conveyor_belt/sausage.sdf",
            ]

            subprocess.run(cmd)

            self.counter += 1

        time.sleep(0.5)

        self.publish_graspable_objects()

        self.get_logger().info("Spawned 4 sausages")

def main():
    rclpy.init()
    node = sausageSpawner()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
