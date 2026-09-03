#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

import subprocess
import time
import random
import math
import json

from std_msgs.msg import String, Float64

from rclpy.qos import (
    QoSProfile,
    ReliabilityPolicy,
    DurabilityPolicy
)


class sausageSpawner(Node):

    def __init__(self):
        super().__init__("sausage_spawner")

        ############################################################
        # CONFIGURACIÓN
        ############################################################

        # Velocidad del conveyor
        self.BELT_SPEED = -0.15

        # Posición de spawn
        self.MIN_X = -0.18
        self.MAX_X = 0.18

        # La Y es SIEMPRE la misma
        self.SPAWN_Y = 0.58

        # Altura de spawn
        self.SPAWN_Z = 0.76

        # Tiempo entre salchichas
        # 2.0 -> una salchicha cada 2 segundos
        self.SPAWN_INTERVAL = 50.0

        # Archivo SDF
        self.SAUSAGE_SDF = (
            "/home/ws/src/CustomRobots/"
            "conveyor_belt/sausage.sdf"
        )

        ############################################################
        # ESTADO
        ############################################################

        self.counter = 0

        # Diccionario con las salchichas generadas
        self.sausages = {}

        # Tiempo del último spawn
        self.last_spawn_time = 0.0

        # Control del conveyor
        self.belt_started = False

        ############################################################
        # PUBLICADORES
        ############################################################

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

        ############################################################
        # TIMER DEL CONVEYOR
        ############################################################

        # Publicamos continuamente la velocidad.
        #
        # Esto hace que el conveyor permanezca moviéndose incluso
        # si otro nodo publica ocasionalmente otra velocidad.
        self.belt_timer = self.create_timer(
            0.01,
            self.update_belt
        )

        ############################################################
        # TIMER DE SPAWN
        ############################################################

        # Comprobamos periódicamente si toca crear otra salchicha.
        self.spawn_timer = self.create_timer(
            0.1,
            self.update_spawn
        )

        ############################################################
        # INICIALIZACIÓN
        ############################################################

        self.get_logger().info(
            "Waiting 5 seconds for Gazebo..."
        )

        time.sleep(5)

        ############################################################
        # PUBLICAR OBJETOS GRASPABLES
        ############################################################

        self.publish_graspable_objects()

        ############################################################
        # ESPERA ANTES DEL PRIMER SPAWN
        ############################################################

        self.get_logger().info(
            "Waiting 20 seconds before spawning the first sausage..."
        )

        time.sleep(20)

        ############################################################
        # PRIMERA SALCHICHA
        ############################################################

        self.spawn_sausage()

        # Guardamos el instante del primer spawn
        self.last_spawn_time = time.monotonic()

        ############################################################
        # ARRANCAR CONVEYOR
        ############################################################

        self.start_belt()

    ############################################################
    # PUBLICAR OBJETOS GRASPABLES
    ############################################################

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

    ############################################################
    # PUBLICAR INFORMACIÓN DE SALCHICHA
    ############################################################

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

    ############################################################
    # ESTABLECER VELOCIDAD DEL CONVEYOR
    ############################################################

    def set_belt(self, speed):

        msg = Float64()

        msg.data = float(speed)

        self.speed_pub.publish(msg)

    ############################################################
    # ARRANCAR CONVEYOR
    ############################################################

    def start_belt(self):

        if self.belt_started:
            return

        self.belt_started = True

        self.get_logger().info(
            f"Starting conveyor at "
            f"{self.BELT_SPEED:.2f} m/s"
        )

    ############################################################
    # ACTUALIZAR CONVEYOR
    ############################################################

    def update_belt(self):

        if not self.belt_started:
            return

        # IMPORTANTE:
        # Nunca ponemos la velocidad a cero.
        #
        # El conveyor recibe continuamente BELT_SPEED.
        self.set_belt(self.BELT_SPEED)

    ############################################################
    # CONTROL DEL SPAWN
    ############################################################

    def update_spawn(self):

        if not self.belt_started:
            return

        now = time.monotonic()

        elapsed = now - self.last_spawn_time

        if elapsed >= self.SPAWN_INTERVAL:

            self.spawn_sausage()

            self.last_spawn_time = now

    ############################################################
    # GENERAR UNA SALCHICHA
    ############################################################

    def spawn_sausage(self):

        ########################################################
        # NOMBRE
        ########################################################

        name = f"box_{self.counter}"

        ########################################################
        # X ALEATORIA
        ########################################################

        x = random.uniform(
            self.MIN_X,
            self.MAX_X
        )

        ########################################################
        # Y FIJA
        ########################################################

        y = self.SPAWN_Y

        ########################################################
        # ORIENTACIÓN ALEATORIA
        ########################################################

        yaw = random.uniform(
            -math.pi,
            math.pi
        )

        ########################################################
        # COMANDO DE SPAWN
        ########################################################

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

        ########################################################
        # EJECUTAR SPAWN
        ########################################################

        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True
        )

        ########################################################
        # COMPROBAR RESULTADO
        ########################################################

        if result.returncode != 0:

            self.get_logger().error(
                f"Failed to spawn {name}: "
                f"{result.stderr.strip()}"
            )

            return

        ########################################################
        # GUARDAR INFORMACIÓN
        ########################################################

        self.sausages[name] = {
            "x": x,
            "y": y,
            "z": self.SPAWN_Z,
            "yaw": yaw
        }

        self.counter += 1

        ########################################################
        # PUBLICAR INFORMACIÓN
        ########################################################

        self.publish_sausage_info(
            name,
            x,
            y,
            yaw
        )

        self.publish_graspable_objects()

        ########################################################
        # LOG
        ########################################################

        self.get_logger().info(
            f"Spawned {name} successfully. "
            f"Total sausages: {self.counter}"
        )

    ############################################################
    # DESTRUIR NODO
    ############################################################

    def destroy_node(self):

        # Aunque el nodo se cierre, dejamos el conveyor parado
        # como medida de seguridad.
        if hasattr(self, "speed_pub"):

            msg = Float64()
            msg.data = 0.0

            self.speed_pub.publish(msg)

        super().destroy_node()


############################################################
# MAIN
############################################################

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