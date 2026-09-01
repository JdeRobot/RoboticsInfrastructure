#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

import subprocess
import time
import random
import math
import json

from std_msgs.msg import String, Float64
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy


class sausageSpawner(Node):

    def __init__(self):
        super().__init__("sausage_spawner")

        self.NUM_SAUSAGES = 4

        self.BELT_SPEED = -0.15

        self.STOP_TIME = 12

        self.MIN_X = -0.18
        self.MAX_X = 0.18

        self.MIN_DISTANCE = 0.08

        # Y inicial
        self.SPAWN_Y = 0.58

        # Diferencia máxima respecto a SPAWN_Y.
        # Siempre será hacia Y = 0.
        self.MAX_Y_OFFSET = 0.15

        self.SPAWN_Z = 0.76

        self.SAUSAGE_SDF = (
            "/home/ws/src/CustomRobots/"
            "conveyor_belt/sausage.sdf"
        )

        self.counter = 0

        self.sausages = {}

        self.belt_started = False

        self.belt_stopped = False

        self.belt_start_time = None

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

        self.belt_timer = self.create_timer(
            0.05,
            self.update_belt
        )

        self.get_logger().info(
            "Waiting 5 seconds for Gazebo..."
        )

        time.sleep(5)

        self.publish_graspable_objects()

        self.get_logger().info(
            "Waiting 20 seconds before spawning sausages..."
        )

        time.sleep(20)

        self.spawn_all_sausages()

    def publish_graspable_objects(self):

        msg = String()

        msg.data = ",".join(
            [f"box_{i}" for i in range(self.counter)]
        )

        self.graspable_pub.publish(msg)

        self.get_logger().info(
            f"Graspable objects -> {msg.data}"
        )

    def publish_sausage_info(self, name):

        if name not in self.sausages:
            return

        sausage = self.sausages[name]

        msg = String()

        msg.data = json.dumps({
            "name": name,
            "x": sausage["x"],
            "y": sausage["y"]
        })

        self.sausage_info_pub.publish(msg)

        self.get_logger().info(
            f"Sausage info -> {msg.data}"
        )

    def set_belt(self, speed):

        msg = Float64()

        msg.data = float(speed)

        self.speed_pub.publish(msg)

        self.get_logger().info(
            f"/conveyor/speed -> {speed:.2f} m/s"
        )

    def start_belt(self):

        if self.belt_started:
            return

        self.belt_started = True

        self.belt_stopped = False

        self.belt_start_time = time.time()

        self.get_logger().info(
            "All sausages spawned."
        )

        self.get_logger().info(
            f"Starting conveyor at "
            f"{self.BELT_SPEED:.2f} m/s"
        )

        self.set_belt(self.BELT_SPEED)

    def update_belt(self):

        if not self.belt_started:
            return

        if self.belt_stopped:
            return

        if self.belt_start_time is None:
            return

        elapsed = (
            time.time() -
            self.belt_start_time
        )

        if elapsed < self.STOP_TIME:
            return

        self.belt_stopped = True

        self.set_belt(0.0)

        self.get_logger().info(
            f"Conveyor stopped after "
            f"{self.STOP_TIME:.1f} seconds."
        )

    def spawn_all_sausages(self):

        NUM_SAUSAGES = self.NUM_SAUSAGES

        # --------------------------------------------------
        # GENERAR X DIFERENTES
        # --------------------------------------------------

        x_positions = []

        while len(x_positions) < NUM_SAUSAGES:

            x = random.uniform(
                self.MIN_X,
                self.MAX_X
            )

            valid = True

            for p in x_positions:

                if abs(x - p) < self.MIN_DISTANCE:

                    valid = False

                    break

            if valid:

                x_positions.append(x)

        # --------------------------------------------------
        # GENERAR Y DIFERENTES
        # --------------------------------------------------
        #
        # Todas parten desde SPAWN_Y = 0.58.
        #
        # Solo permitimos desplazamiento hacia Y = 0:
        #
        # 0.58
        # 0.56
        # 0.54
        # 0.52
        #
        # Nunca:
        #
        # 0.60
        # 0.62
        #
        # --------------------------------------------------

        y_positions = [
            self.SPAWN_Y - random.uniform(
                0.0,
                self.MAX_Y_OFFSET
            )
            for _ in range(NUM_SAUSAGES)
        ]

        # Intentamos que las Y sean diferentes.
        y_positions = sorted(y_positions, reverse=True)

        # --------------------------------------------------
        # NOMBRES
        # --------------------------------------------------

        box_names = [
            f"box_{i}"
            for i in range(NUM_SAUSAGES)
        ]

        random.shuffle(box_names)

        # --------------------------------------------------
        # SPAWN DE LAS 4 SALCHICHAS
        # --------------------------------------------------
        #
        # NO HAY NINGÚN DELAY ENTRE ELLAS.
        # Se ejecutan una detrás de otra inmediatamente.
        #
        # --------------------------------------------------

        for i in range(NUM_SAUSAGES):

            x = x_positions[i]
            y = y_positions[i]

            name = box_names[i]

            yaw = random.uniform(
                -math.pi,
                math.pi
            )

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

                continue

            self.sausages[name] = {
                "x": x,
                "y": y
            }

            self.counter += 1

            self.publish_sausage_info(name)

            self.get_logger().info(
                f"Spawned {name} "
                f"at x={x:.3f}, "
                f"y={y:.3f}"
            )

        # --------------------------------------------------
        # PUBLICAR OBJETOS
        # --------------------------------------------------

        self.publish_graspable_objects()

        # --------------------------------------------------
        # ARRANCAR CINTA DESPUÉS DE SPAWNEAR TODAS
        # --------------------------------------------------

        if self.counter > 0:
            self.start_belt()

        self.get_logger().info(
            f"Spawned {self.counter} sausages."
        )

    def destroy_node(self):

        if hasattr(self, "speed_pub"):

            self.set_belt(0.0)

        super().destroy_node()


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