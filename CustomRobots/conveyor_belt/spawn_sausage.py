#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

import subprocess
import time
import random
import math

from std_msgs.msg import String, Float64


class sausageSpawner(Node):

    def __init__(self):
        super().__init__("sausage_spawner")

        # ==========================================================
        # CONFIGURACIÓN
        # ==========================================================

        self.NUM_SAUSAGES = 4

        # Velocidad de la cinta.
        # -0.15 -> dirección -Y
        self.BELT_SPEED = -0.15

        # Tiempo que permanece funcionando la cinta
        # desde que aparece la primera salchicha.
        self.STOP_TIME = 13.0

        # Posiciones de spawn
        self.MIN_X = -0.18
        self.MAX_X = 0.18

        # Distancia mínima entre salchichas
        self.MIN_DISTANCE = 0.08

        # Posición inicial Y
        self.SPAWN_Y = 0.58

        # Posición inicial Z
        self.SPAWN_Z = 0.76

        # Ruta del modelo
        self.SAUSAGE_SDF = (
            "/home/ws/src/CustomRobots/"
            "conveyor_belt/sausage.sdf"
        )


        # ==========================================================
        # ESTADO
        # ==========================================================

        self.counter = 0

        # Indica si ya ha aparecido la primera salchicha
        self.belt_started = False

        # Indica si ya hemos detenido la cinta
        self.belt_stopped = False

        # Instante en el que comenzó la cinta
        self.belt_start_time = None


        # ==========================================================
        # PUBLICADOR DE OBJETOS AGARRABLES
        # ==========================================================

        self.graspable_pub = self.create_publisher(
            String,
            "/graspable_objects",
            10
        )


        # ==========================================================
        # PUBLICADOR DE LA CINTA
        # ==========================================================

        # EXACTAMENTE igual que el ejercicio de paletizado:
        #
        # ROS:
        #   /conveyor/speed
        #
        # ros_gz_bridge:
        #   /conveyor/speed
        #          ↓
        #   /model/conveyor_belt_1/link/link/track_cmd_vel
        #
        # Gazebo:
        #   TrackController

        self.speed_pub = self.create_publisher(
            Float64,
            "/conveyor/speed",
            10
        )


        # ==========================================================
        # TIMER PARA PARAR LA CINTA
        # ==========================================================

        # Lo creamos ANTES del spawn.
        #
        # Importante: aunque spawn_all_sausages usa esperas,
        # el inicio de la cinta se hace directamente después
        # del primer spawn, no depende de este timer.

        self.belt_timer = self.create_timer(
            0.05,
            self.update_belt
        )


        # ==========================================================
        # ESPERAR A QUE GAZEBO ESTÉ LISTO
        # ==========================================================

        self.get_logger().info(
            "Waiting 5 seconds for Gazebo..."
        )

        time.sleep(5)


        # ==========================================================
        # PUBLICAR LISTA INICIAL
        # ==========================================================

        self.publish_graspable_objects()


        # ==========================================================
        # ESPERAR ANTES DE SPAWNEAR
        # ==========================================================

        self.get_logger().info(
            "Waiting 20 seconds before spawning sausages..."
        )

        time.sleep(20)


        # ==========================================================
        # SPAWN
        # ==========================================================

        self.spawn_all_sausages()


    # ==============================================================
    # PUBLICAR OBJETOS AGARRABLES
    # ==============================================================

    def publish_graspable_objects(self):

        msg = String()

        msg.data = ",".join(
            [f"box_{i}" for i in range(self.counter)]
        )

        self.graspable_pub.publish(msg)

        self.get_logger().info(
            f"Graspable objects -> {msg.data}"
        )


    # ==============================================================
    # CONTROL DE LA CINTA
    # ==============================================================

    def set_belt(self, speed):

        msg = Float64()

        msg.data = float(speed)

        self.speed_pub.publish(msg)

        self.get_logger().info(
            f"/conveyor/speed -> {speed:.2f} m/s"
        )


    # ==============================================================
    # ARRANCAR CINTA
    # ==============================================================

    def start_belt(self):

        if self.belt_started:
            return

        self.belt_started = True

        self.belt_stopped = False

        self.belt_start_time = time.time()


        self.get_logger().info(
            "First sausage spawned."
        )

        self.get_logger().info(
            f"Starting conveyor at "
            f"{self.BELT_SPEED:.2f} m/s"
        )


        # EXACTAMENTE el equivalente a:
        #
        # self._set_belt(self.belt_speed)
        #
        # del ejercicio de paletizado.

        self.set_belt(self.BELT_SPEED)


    # ==============================================================
    # COMPROBAR TIEMPO DE FUNCIONAMIENTO
    # ==============================================================

    def update_belt(self):

        # Todavía no ha aparecido ninguna salchicha.
        if not self.belt_started:
            return

        # Ya está parada.
        if self.belt_stopped:
            return

        if self.belt_start_time is None:
            return


        elapsed = (
            time.time() -
            self.belt_start_time
        )


        # Todavía debe funcionar.
        if elapsed < self.STOP_TIME:
            return


        # ==========================================================
        # PARAR CINTA
        # ==========================================================

        self.belt_stopped = True

        self.set_belt(0.0)

        self.get_logger().info(
            f"Conveyor stopped after "
            f"{self.STOP_TIME:.1f} seconds."
        )


    # ==============================================================
    # SPAWN DE SALCHICHAS
    # ==============================================================

    def spawn_all_sausages(self):

        NUM_SAUSAGES = self.NUM_SAUSAGES


        # ==========================================================
        # GENERAR POSICIONES X
        # ==========================================================

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


        # ==========================================================
        # TIEMPOS DE APARICIÓN
        # ==========================================================

        spawn_times = sorted(
            random.uniform(0.0, 2.0)
            for _ in range(NUM_SAUSAGES)
        )


        # ==========================================================
        # NOMBRES ALEATORIOS
        # ==========================================================

        box_names = [
            f"box_{i}"
            for i in range(NUM_SAUSAGES)
        ]

        random.shuffle(box_names)


        # ==========================================================
        # COMENZAR CRONÓMETRO
        # ==========================================================

        start_time = time.time()


        # ==========================================================
        # GENERAR SALCHICHAS
        # ==========================================================

        for i, x in enumerate(positions):


            # ------------------------------------------------------
            # ESPERAR AL INSTANTE DE SPAWN
            # ------------------------------------------------------

            target_time = (
                start_time +
                spawn_times[i]
            )


            while time.time() < target_time:

                time.sleep(0.005)


            # ------------------------------------------------------
            # NOMBRE
            # ------------------------------------------------------

            name = box_names[i]


            # ------------------------------------------------------
            # ORIENTACIÓN ALEATORIA
            # ------------------------------------------------------

            yaw = random.uniform(
                -math.pi,
                math.pi
            )


            # ------------------------------------------------------
            # COMANDO DE SPAWN
            # ------------------------------------------------------

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


            # ------------------------------------------------------
            # EJECUTAR SPAWN
            # ------------------------------------------------------

            result = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True
            )


            # ------------------------------------------------------
            # COMPROBAR ERROR
            # ------------------------------------------------------

            if result.returncode != 0:

                self.get_logger().error(
                    f"Failed to spawn {name}: "
                    f"{result.stderr.strip()}"
                )

                continue


            # ------------------------------------------------------
            # SALCHICHA CREADA
            # ------------------------------------------------------

            self.get_logger().info(
                f"Spawned {name} "
                f"at x={x:.3f} "
                f"t={spawn_times[i]:.2f}s"
            )


            self.counter += 1


            # ------------------------------------------------------
            # PRIMERA SALCHICHA
            # ------------------------------------------------------

            # IMPORTANTÍSIMO:
            #
            # Arrancamos la cinta inmediatamente después
            # de crear la primera salchicha.
            #
            # No esperamos a que aparezcan las otras 3.

            if self.counter == 1:

                self.start_belt()


        # ==========================================================
        # PUBLICAR OBJETOS AGARRABLES
        # ==========================================================

        self.publish_graspable_objects()


        self.get_logger().info(
            f"Spawned {NUM_SAUSAGES} sausages."
        )


    # ==============================================================
    # DESTRUCCIÓN
    # ==============================================================

    def destroy_node(self):

        # Asegurar que la cinta queda parada.

        if hasattr(self, "speed_pub"):

            self.set_belt(0.0)


        super().destroy_node()


# ==================================================================
# MAIN
# ==================================================================

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