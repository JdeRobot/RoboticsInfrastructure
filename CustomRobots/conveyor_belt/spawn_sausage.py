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

from gz.msgs10.pose_v_pb2 import Pose_V
from gz.transport13 import Node as GazeboNode, SubscribeOptions


class sausageSpawner(Node):

    def __init__(self):
        super().__init__("sausage_spawner")

        self.NUM_SAUSAGES = 4

        self.BELT_SPEED = -0.1

        # Y a la que se detendrá la cinta
        self.STOP_Y = -0.50

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

        self.reference_y = None

        # --------------------------------------------------
        # SEGUIMIENTO DE POSICIÓN DE LAS SALCHICHAS
        # --------------------------------------------------

        self.active_sausage = None

        self.sausage_position = None

        self.position_sample_period = 0.01

        self.last_position_sample_time = 0.0

        self.gazebo_node = GazeboNode()

        options = SubscribeOptions()

        options.msgs_per_sec = 100

        self.gazebo_node.subscribe(
            Pose_V,
            "/world/default/dynamic_pose/info",
            self.update_sausage_position,
            options
        )

        self.belt_started = False

        self.belt_stopped = False

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
            0.01,
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

    def update_sausage_position(self, message):

        now = time.monotonic()

        # Limitar la frecuencia de actualización
        if (
            self.active_sausage is None
            or now - self.last_position_sample_time
            < self.position_sample_period
        ):
            return

        self.last_position_sample_time = now

        # Buscar nuestra salchicha dentro de las poses de Gazebo
        for pose in message.pose:

            if pose.name == self.active_sausage:

                self.sausage_position = {
                    "x": float(pose.position.x),
                    "y": float(pose.position.y),
                    "z": float(pose.position.z)
                }

                self.get_logger().info(
                    f"{self.active_sausage} position -> "
                    f"x={pose.position.x:.3f}, "
                    f"y={pose.position.y:.3f}, "
                    f"z={pose.position.z:.3f}"
                )

                return

    def track_sausage(self, name):

        self.active_sausage = name

        self.sausage_position = None

        self.last_position_sample_time = 0.0

        self.get_logger().info(
            f"Tracking sausage: {name}"
        )

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

        y_difference = abs(
            sausage["y"] - self.reference_y
        )

        msg = String()

        msg.data = json.dumps({
            "name": name,
            "x": sausage["x"],
            "y": sausage["y"],
            "y_difference": y_difference
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

        self.get_logger().info(
            "All sausages spawned."
        )

        self.get_logger().info(
            f"Starting conveyor at "
            f"{self.BELT_SPEED:.2f} m/s"
        )

        self.get_logger().info(
            f"Conveyor will stop when "
            f"{self.active_sausage} reaches "
            f"Y <= {self.STOP_Y:.3f}"
        )

        self.set_belt(self.BELT_SPEED)

    def update_belt(self):

        if not self.belt_started:
            return

        if self.belt_stopped:
            return

        # Todavía no tenemos una salchicha trackeada
        if self.active_sausage is None:
            return

        # Todavía no tenemos su posición
        if self.sausage_position is None:
            return

        current_y = self.sausage_position["y"]

        # Comprobar si la salchicha trackeada
        # ha llegado a la posición objetivo
        if current_y <= self.STOP_Y:

            self.belt_stopped = True

            self.set_belt(0.0)

            self.get_logger().info(
                f"Conveyor stopped. "
                f"{self.active_sausage} reached "
                f"Y={current_y:.3f} "
                f"(target Y={self.STOP_Y:.3f})"
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

        # Índice de la salchicha cuya Y está más cerca de 0
        closest_y_index = min(
            range(NUM_SAUSAGES),
            key=lambda i: abs(y_positions[i])
        )

        self.reference_y = y_positions[closest_y_index]

        self.get_logger().info(
            f"Reference sausage Y = {self.reference_y:.3f}"
        )

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

            if i == closest_y_index:
                self.track_sausage(name)

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