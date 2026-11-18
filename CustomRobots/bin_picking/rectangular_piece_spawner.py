
#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

import subprocess
import time
import random
import math

from std_msgs.msg import String


class rectangularPieceSpawner(Node):

    def __init__(self):
        super().__init__("rectangular_piece_spawner")

        # ==========================================
        # CONFIGURACION DEL SPAWNER
        # ==========================================

        self.NUM_PIECES = 4

        # Dimensiones de la pieza
        self.PIECE_X = 0.030
        self.PIECE_Y = 0.020
        self.PIECE_Z = 0.055

        # Contenedor
        self.BOX_CENTER_X = -0.5
        self.BOX_CENTER_Y = 0.0

        self.BOX_INNER_X = 0.47
        self.BOX_INNER_Y = 0.37

        # Posiciones permitidas para el centro de las piezas.
        # Se deja margen para que no toquen las paredes.

        self.MIN_X = -0.70
        self.MAX_X = -0.30

        self.MIN_Y = -0.15
        self.MAX_Y = 0.15

        # Altura de la superficie interior del contenedor
        self.FLOOR_Z = 0.78

        # Separacion minima entre centros de piezas
        self.MIN_DISTANCE = 0.05

        # Numero maximo de intentos para encontrar posiciones
        self.MAX_ATTEMPTS = 1000

        # Archivo SDF
        self.PIECE_SDF = (
            "/home/ws/src/CustomRobots/"
            "bin_picking/rectangular_piece.sdf"
        )

        # ==========================================
        # VARIABLES
        # ==========================================

        self.counter = 0
        self.pieces = {}

        # ==========================================
        # PUBLICADORES
        # ==========================================

        self.graspable_pub = self.create_publisher(
            String,
            "/graspable_objects",
            10
        )

        # ==========================================
        # INICIO
        # ==========================================

        self.get_logger().info(
            "Waiting 5 seconds for Gazebo..."
        )

        time.sleep(5)

        self.get_logger().info(
            "Waiting 3 seconds before spawning pieces..."
        )

        time.sleep(3)

        self.spawn_all_pieces()

    # ==============================================
    # PUBLICAR PIEZAS DETECTABLES / AGARRABLES
    # ==============================================

    def publish_graspable_objects(self):

        msg = String()

        msg.data = ",".join(
            [f"piece_{i}" for i in range(self.counter)]
        )

        self.graspable_pub.publish(msg)

        self.get_logger().info(
            f"Graspable objects -> {msg.data}"
        )

    # ==============================================
    # GENERAR POSICIONES ALEATORIAS
    # ==============================================

    def generate_positions(self):

        positions = []

        attempts = 0

        while (
            len(positions) < self.NUM_PIECES
            and attempts < self.MAX_ATTEMPTS
        ):

            attempts += 1

            x = random.uniform(
                self.MIN_X,
                self.MAX_X
            )

            y = random.uniform(
                self.MIN_Y,
                self.MAX_Y
            )

            valid = True

            # Comprobar distancia respecto a las piezas anteriores
            for p in positions:

                distance = math.sqrt(
                    (x - p["x"]) ** 2 +
                    (y - p["y"]) ** 2
                )

                if distance < self.MIN_DISTANCE:
                    valid = False
                    break

            if valid:

                positions.append({
                    "x": x,
                    "y": y
                })

        if len(positions) < self.NUM_PIECES:

            self.get_logger().error(
                "Could not generate enough valid positions."
            )

        return positions

    # ==============================================
    # SPAWNEAR TODAS LAS PIEZAS
    # ==============================================

    def spawn_all_pieces(self):

        positions = self.generate_positions()

        for i, position in enumerate(positions):

            name = f"piece_{i}"

            x = position["x"]
            y = position["y"]

            # Orientacion aleatoria alrededor del eje Z
            roll = 0.0
            pitch = 0.0

            yaw = random.uniform(
                -math.pi,
                math.pi
            )

            # Centro de la pieza:
            # mitad de su altura por encima del suelo
            z = self.FLOOR_Z + self.PIECE_Z / 2.0

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
                str(z),

                "-R",
                str(roll),

                "-P",
                str(pitch),

                "-Y",
                str(yaw),

                "-file",
                self.PIECE_SDF,
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

            self.pieces[name] = {
                "x": x,
                "y": y,
                "z": z,
                "roll": roll,
                "pitch": pitch,
                "yaw": yaw
            }

            self.counter += 1

            self.get_logger().info(
                f"Spawned {name} "
                f"at x={x:.3f}, "
                f"y={y:.3f}, "
                f"z={z:.3f}, "
                f"yaw={yaw:.3f}"
            )

        # Publicar nombres de las piezas
        self.publish_graspable_objects()

        self.get_logger().info(
            f"Spawned {self.counter} rectangular pieces."
        )


def main():

    rclpy.init()

    node = rectangularPieceSpawner()

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
