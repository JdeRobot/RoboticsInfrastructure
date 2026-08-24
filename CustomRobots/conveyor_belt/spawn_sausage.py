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
        #self.timer = self.create_timer(7.0, self.spawn_sausage)
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

        # ==========================================================
        # Instantes de aparición de las 4 salchichas.
        # Todas aparecerán dentro del intervalo [0, 1] segundos.
        # ==========================================================

        spawn_times = sorted(
            random.uniform(0.0, 1.0)
            for _ in range(NUM_SAUSAGES)
        )

        start_time = time.time()

        for i, x in enumerate(positions):

            # Esperar hasta el instante de aparición correspondiente
            target_time = start_time + spawn_times[i]

            while time.time() < target_time:
                time.sleep(0.005)

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

            self.get_logger().info(
                f"Spawned {name} at t={spawn_times[i]:.2f}s"
            )

            self.counter += 1

        self.publish_graspable_objects()

        self.get_logger().info(
            "Spawned 4 sausages within the first second"
        )

def main():
    rclpy.init()
    node = sausageSpawner()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
