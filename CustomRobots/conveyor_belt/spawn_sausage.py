#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

import subprocess
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
        # USAR TIEMPO DE SIMULACIÓN
        ############################################################

        self.declare_parameter(
            "use_sim_time",
            True
        )

        ############################################################
        # CONFIGURACIÓN
        ############################################################

        self.NUM_SAUSAGES = 4

        self.BELT_SPEED = -0.15

        # Tiempo SIMULADO desde que aparece la primera salchicha
        # hasta que se detiene la cinta.
        self.STOP_TIME = 12.0

        self.MIN_X = -0.18
        self.MAX_X = 0.18

        self.MIN_DISTANCE = 0.08

        self.SPAWN_Y = 0.58

        self.SPAWN_Z = 0.76

        self.SAUSAGE_SDF = (
            "/home/ws/src/CustomRobots/"
            "conveyor_belt/sausage.sdf"
        )

        ############################################################
        # ESTADO
        ############################################################

        self.counter = 0

        self.sausages = {}

        self.belt_started = False

        self.belt_stopped = False

        self.belt_start_time = None

        ############################################################
        # ESTADO DEL SPAWNER
        ############################################################

        # Esperamos inicialmente 5 segundos SIMULADOS
        self.startup_wait = 5.0

        # Después esperamos 20 segundos SIMULADOS
        # antes de generar las salchichas.
        self.spawn_wait = 20.0

        self.initial_time = None

        self.spawn_start_time = None

        self.spawning = False

        self.spawn_times = []

        self.spawn_positions = []

        self.spawn_index = 0

        self.box_names = []

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
        # TIMER
        ############################################################

        self.timer = self.create_timer(
            0.05,
            self.update
        )

        ############################################################
        # TIEMPO SIMULADO INICIAL
        ############################################################

        self.initial_time = self.sim_time()

        self.get_logger().info(
            "Sausage spawner iniciado."
        )

        self.get_logger().info(
            "Esperando 5 segundos de TIEMPO SIMULADO..."
        )

    ############################################################
    # TIEMPO DE SIMULACIÓN
    ############################################################

    def sim_time(self):

        return (
            self.get_clock().now().nanoseconds
            / 1e9
        )

    ############################################################
    # ACTUALIZACIÓN PRINCIPAL
    ############################################################

    def update(self):

        current_time = self.sim_time()

        ########################################################
        # 1. ESPERA INICIAL
        ########################################################

        if self.counter == 0 and not self.spawning:

            elapsed = (
                current_time -
                self.initial_time
            )

            if elapsed < self.startup_wait:
                return

            self.get_logger().info(
                "Han pasado 5 segundos SIMULADOS."
            )

            self.publish_graspable_objects()

            self.spawn_start_time = current_time

            self.get_logger().info(
                "Esperando 20 segundos de TIEMPO SIMULADO "
                "antes de generar las salchichas..."
            )

            # Marcamos que estamos en la fase de espera
            self.spawning = True

            # Usamos un índice especial para distinguir
            # espera inicial de generación.
            self.spawn_index = -1

            return

        ########################################################
        # 2. ESPERA DE 20 SEGUNDOS SIMULADOS
        ########################################################

        if self.spawning and self.spawn_index == -1:

            elapsed = (
                current_time -
                self.spawn_start_time
            )

            if elapsed < self.spawn_wait:
                return

            self.get_logger().info(
                "Han pasado 20 segundos SIMULADOS."
            )

            self.prepare_spawning()

            return

        ########################################################
        # 3. GENERAR SALCHICHAS
        ########################################################

        if self.spawning:

            self.update_spawning(
                current_time
            )

        ########################################################
        # 4. CONTROL DE LA CINTA
        ########################################################

        self.update_belt()

    ############################################################
    # PREPARAR GENERACIÓN
    ############################################################

    def prepare_spawning(self):

        NUM_SAUSAGES = self.NUM_SAUSAGES

        ########################################################
        # POSICIONES X
        ########################################################

        positions = []

        while len(positions) < NUM_SAUSAGES:

            x = random.uniform(
                self.MIN_X,
                self.MAX_X
            )

            valid = True

            for p in positions:

                if abs(x - p) < self.MIN_DISTANCE:

                    valid = False
                    break

            if valid:
                positions.append(x)

        ########################################################
        # TIEMPOS DE APARICIÓN
        #
        # También son TIEMPO SIMULADO
        ########################################################

        self.spawn_times = sorted(
            random.uniform(0.0, 2.0)
            for _ in range(NUM_SAUSAGES)
        )

        ########################################################
        # NOMBRES
        ########################################################

        self.box_names = [
            f"box_{i}"
            for i in range(NUM_SAUSAGES)
        ]

        random.shuffle(
            self.box_names
        )

        ########################################################
        # GUARDAR POSICIONES
        ########################################################

        self.spawn_positions = positions

        self.spawn_start_time = self.sim_time()

        self.spawn_index = 0

        self.get_logger().info(
            "Comenzando generación de salchichas."
        )

    ############################################################
    # GENERAR SALCHICHAS SEGÚN TIEMPO SIMULADO
    ############################################################

    def update_spawning(self, current_time):

        if self.spawn_index >= self.NUM_SAUSAGES:

            self.spawning = False

            self.publish_graspable_objects()

            self.get_logger().info(
                f"Spawn completado: "
                f"{self.NUM_SAUSAGES} salchichas."
            )

            return

        elapsed = (
            current_time -
            self.spawn_start_time
        )

        target_time = self.spawn_times[
            self.spawn_index
        ]

        ########################################################
        # TODAVÍA NO TOCA GENERAR
        ########################################################

        if elapsed < target_time:
            return

        ########################################################
        # GENERAR
        ########################################################

        x = self.spawn_positions[
            self.spawn_index
        ]

        name = self.box_names[
            self.spawn_index
        ]

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
            str(self.SPAWN_Y),

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

        else:

            self.sausages[name] = {
                "x": x
            }

            self.counter += 1

            ####################################################
            # LA CINTA COMIENZA CON LA PRIMERA SALCHICHA
            ####################################################

            if self.counter == 1:

                self.start_belt()

            self.publish_sausage_info(
                name
            )

            self.get_logger().info(
                f"Spawned {name} "
                f"at x={x:.3f} "
                f"t={target_time:.2f}s SIM"
            )

        ########################################################
        # SIGUIENTE
        ########################################################

        self.spawn_index += 1

    ############################################################
    # PUBLICAR OBJETOS
    ############################################################

    def publish_graspable_objects(self):

        msg = String()

        msg.data = ",".join(
            [
                f"box_{i}"
                for i in range(self.counter)
            ]
        )

        self.graspable_pub.publish(
            msg
        )

        self.get_logger().info(
            f"Graspable objects -> {msg.data}"
        )

    ############################################################
    # INFORMACIÓN DE SALCHICHA
    ############################################################

    def publish_sausage_info(self, name):

        if name not in self.sausages:
            return

        sausage = self.sausages[name]

        msg = String()

        msg.data = json.dumps({
            "name": name,
            "x": sausage["x"]
        })

        self.sausage_info_pub.publish(
            msg
        )

        self.get_logger().info(
            f"Sausage info -> {msg.data}"
        )

    ############################################################
    # CONTROL VELOCIDAD CINTA
    ############################################################

    def set_belt(self, speed):

        msg = Float64()

        msg.data = float(speed)

        self.speed_pub.publish(
            msg
        )

        self.get_logger().info(
            f"/conveyor/speed -> "
            f"{speed:.2f} m/s"
        )

    ############################################################
    # ARRANCAR CINTA
    ############################################################

    def start_belt(self):

        if self.belt_started:
            return

        self.belt_started = True

        self.belt_stopped = False

        ########################################################
        # TIEMPO DE SIMULACIÓN
        ########################################################

        self.belt_start_time = self.sim_time()

        self.get_logger().info(
            "Primera salchicha spawned."
        )

        self.get_logger().info(
            f"Iniciando conveyor a "
            f"{self.BELT_SPEED:.2f} m/s"
        )

        self.get_logger().info(
            f"Tiempo simulado inicial: "
            f"{self.belt_start_time:.3f} s"
        )

        self.set_belt(
            self.BELT_SPEED
        )

    ############################################################
    # ACTUALIZAR CINTA
    ############################################################

    def update_belt(self):

        if not self.belt_started:
            return

        if self.belt_stopped:
            return

        if self.belt_start_time is None:
            return

        ########################################################
        # TIEMPO SIMULADO
        ########################################################

        current_time = self.sim_time()

        elapsed = (
            current_time -
            self.belt_start_time
        )

        ########################################################
        # TODAVÍA NO PARAR
        ########################################################

        if elapsed < self.STOP_TIME:
            return

        ########################################################
        # PARAR
        ########################################################

        self.belt_stopped = True

        self.set_belt(0.0)

        self.get_logger().info(
            f"Conveyor detenido después de "
            f"{elapsed:.3f} s de SIM TIME."
        )

    ############################################################
    # DESTRUCCIÓN
    ############################################################

    def destroy_node(self):

        if hasattr(
            self,
            "speed_pub"
        ):

            self.set_belt(0.0)

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