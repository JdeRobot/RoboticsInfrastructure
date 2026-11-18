
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
        # CONFIGURACION GENERAL
        # ==========================================

        # Numero total de piezas
        self.NUM_PIECES = 200

        # Numero de piezas por grupo de spawn
        # Cada grupo se genera a una altura diferente
        self.PIECES_PER_GROUP = 50

        # ==========================================
        # DIMENSIONES DE LAS PIEZAS (metros)
        # ==========================================

        self.PIECE_X = 0.050
        self.PIECE_Y = 0.040
        self.PIECE_Z = 0.075

        # Separacion minima entre piezas al generarlas
        self.MIN_GAP = 0.001

        # ==========================================
        # DIMENSIONES DEL CONTENEDOR
        # ==========================================

        self.BOX_CENTER_X = -0.5
        self.BOX_CENTER_Y = 0.0

        # Dimensiones interiores de la caja
        self.BOX_INNER_X = 0.47
        self.BOX_INNER_Y = 0.37

        # Altura del fondo interior
        self.FLOOR_Z = 0.78

        # Altura de las paredes
        self.BOX_HEIGHT = 0.20

        # Parte superior de las paredes
        self.BOX_TOP_Z = (
            self.FLOOR_Z + self.BOX_HEIGHT
        )

        # ==========================================
        # ZONAS DE SPAWN
        # ==========================================

        # Las piezas aparecen por encima de las paredes
        self.SPAWN_BASE_Z = self.BOX_TOP_Z + 0.12

        # Separacion vertical entre grupos
        # Debe ser mayor que la altura de la pieza
        self.SPAWN_GROUP_SEPARATION = 0.070

        # Pequeña variacion vertical aleatoria
        self.SPAWN_Z_JITTER = 0.010

        # ==========================================
        # LIMITES DE GENERACION
        # ==========================================

        # Centro permitido dentro de la caja
        self.MIN_X = (
            self.BOX_CENTER_X - self.BOX_INNER_X / 2.0
        )

        self.MAX_X = (
            self.BOX_CENTER_X + self.BOX_INNER_X / 2.0
        )

        self.MIN_Y = (
            self.BOX_CENTER_Y - self.BOX_INNER_Y / 2.0
        )

        self.MAX_Y = (
            self.BOX_CENTER_Y + self.BOX_INNER_Y / 2.0
        )

        # Intentos maximos para encontrar posiciones
        self.MAX_ATTEMPTS = 10000

        # ==========================================
        # ARCHIVO SDF
        # ==========================================

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
    # COMPROBAR SI DOS RECTANGULOS SE SOLAPAN
    # ==============================================

    def overlaps(self, candidate, existing):

        # Se comprueba el bounding box alineado con los ejes.
        # Es una comprobacion conservadora para evitar
        # solapamientos entre piezas antes del spawn.

        return (
            abs(candidate["x"] - existing["x"])
            < candidate["half_x"] + existing["half_x"]
            and
            abs(candidate["y"] - existing["y"])
            < candidate["half_y"] + existing["half_y"]
        )

    # ==============================================
    # GENERAR POSICIONES ALEATORIAS PARA UN GRUPO
    # ==============================================

    def generate_positions(self, number_of_pieces):

        positions = []

        attempts = 0

        while (
            len(positions) < number_of_pieces
            and attempts < self.MAX_ATTEMPTS
        ):

            attempts += 1

            # Orientacion aleatoria alrededor de Z
            yaw = random.uniform(
                -math.pi,
                math.pi
            )

            # Semidimensiones de la pieza
            half_x = self.PIECE_X / 2.0
            half_y = self.PIECE_Y / 2.0

            # Bounding box de la pieza rotada
            cos_yaw = abs(math.cos(yaw))
            sin_yaw = abs(math.sin(yaw))

            rotated_half_x = (
                cos_yaw * half_x
                + sin_yaw * half_y
                + self.MIN_GAP / 2.0
            )

            rotated_half_y = (
                sin_yaw * half_x
                + cos_yaw * half_y
                + self.MIN_GAP / 2.0
            )

            # Posicion aleatoria dentro de la caja
            x = random.uniform(
                self.MIN_X + rotated_half_x,
                self.MAX_X - rotated_half_x
            )

            y = random.uniform(
                self.MIN_Y + rotated_half_y,
                self.MAX_Y - rotated_half_y
            )

            candidate = {
                "x": x,
                "y": y,
                "yaw": yaw,
                "half_x": rotated_half_x,
                "half_y": rotated_half_y
            }

            valid = True

            # Comprobar solapamientos con las piezas
            # que pertenecen al mismo grupo

            for existing in positions:

                if self.overlaps(candidate, existing):

                    valid = False
                    break

            if valid:
                positions.append(candidate)

        if len(positions) < number_of_pieces:

            self.get_logger().error(
                f"Could only generate {len(positions)} "
                f"of {number_of_pieces} positions."
            )

        return positions

    # ==============================================
    # SPAWNEAR UNA PIEZA
    # ==============================================

    def spawn_piece(self, name, position, z):

        x = position["x"]
        y = position["y"]
        yaw = position["yaw"]

        # Mantenemos la pieza vertical
        roll = 0.0
        pitch = 0.0

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

            return False

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

        return True

    # ==============================================
    # SPAWNEAR TODAS LAS PIEZAS
    # ==============================================

    def spawn_all_pieces(self):

        self.get_logger().info(
            f"Starting simultaneous spawn of {self.NUM_PIECES} pieces."
        )

        positions = []

        # Generar todas las posiciones antes de crear las piezas
        for i in range(self.NUM_PIECES):

            x = random.uniform(
                self.MIN_X + self.PIECE_X,
                self.MAX_X - self.PIECE_X
            )

            y = random.uniform(
                self.MIN_Y + self.PIECE_Y,
                self.MAX_Y - self.PIECE_Y
            )

            yaw = random.uniform(-math.pi, math.pi)

            # Distribuir las piezas por diferentes alturas
            z = random.uniform(
                self.FLOOR_Z + self.PIECE_Z / 2.0,
                self.BOX_TOP_Z + 0.10
            )

            positions.append({
                "x": x,
                "y": y,
                "z": z,
                "yaw": yaw
            })

        # Crear todas las piezas sin pausas entre ellas
        for i, position in enumerate(positions):

            name = f"piece_{i}"

            success = self.spawn_piece(
                name,
                position,
                position["z"]
            )

            if not success:
                continue

        self.publish_graspable_objects()

        self.get_logger().info(
            f"Spawned {self.counter} rectangular pieces."
        )


# ==============================================
# MAIN
# ==============================================

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
