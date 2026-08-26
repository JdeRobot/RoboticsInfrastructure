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

        # Tiempo inicial para permitir que Gazebo arranque.
        time.sleep(5)

        # Número de salchichas.
        self.NUM_SAUSAGES = 4

        # Velocidad de la cinta.
        #
        # Negativa porque queremos desplazamiento en -Y.
        self.BELT_SPEED = -0.15

        # Tiempo que la cinta permanece funcionando
        # desde que aparece la primera salchicha.
        self.STOP_TIME = 10.0

        # Estado de la cinta.
        self.belt_started = False
        self.belt_stopped = False

        # Instante en el que aparece la primera salchicha.
        self.belt_start_time = None


        # ==========================================================
        # CONTADOR
        # ==========================================================

        self.counter = 0


        # ==========================================================
        # PUBLICADOR DE OBJETOS AGARRABLES
        # ==========================================================

        self.graspable_pub = self.create_publisher(
            String,
            "/graspable_objects",
            10
        )


        # ==========================================================
        # PUBLICADOR DE VELOCIDAD DE LA CINTA
        # ==========================================================

        # Igual que en el ejercicio de paletizado:
        #
        # /conveyor/speed
        #
        # ros_gz_bridge se encargará de convertir:
        #
        # /conveyor/speed
        #
        # en:
        #
        # /model/conveyor_belt_1/link/link/track_cmd_vel

        self.speed_pub = self.create_publisher(
            Float64,
            "/conveyor/speed",
            10
        )


        # Publicar inicialmente la lista de objetos agarrables.
        self.publish_graspable_objects()


        # ==========================================================
        # ESPERAR ANTES DE SPAWNEAR
        # ==========================================================

        time.sleep(20)


        # ==========================================================
        # CREAR LAS SALCHICHAS
        # ==========================================================

        self.spawn_all_sausages()


        # ==========================================================
        # TIMER PARA CONTROLAR LA CINTA
        # ==========================================================

        self.belt_timer = self.create_timer(
            0.05,
            self.update_belt
        )


    # ==============================================================
    # PUBLICAR OBJETOS AGARRABLES
    # ==============================================================

    def publish_graspable_objects(self):

        msg = String()

        msg.data = ",".join(
            [f"box_{i}" for i in range(self.counter)]
        )

        self.graspable_pub.publish(msg)


    # ==============================================================
    # CONTROL DE LA CINTA
    # ==============================================================

    def set_belt(self, speed):

        msg = Float64()

        msg.data = float(speed)

        self.speed_pub.publish(msg)

        self.get_logger().info(
            f"Belt speed -> {speed:.2f} m/s"
        )


    # ==============================================================
    # CONTROL TEMPORAL DE LA CINTA
    # ==============================================================

    def update_belt(self):

        # ----------------------------------------------------------
        # Todavía no ha aparecido ninguna salchicha.
        # ----------------------------------------------------------

        if self.counter == 0:
            return


        # ----------------------------------------------------------
        # PRIMERA SALCHICHA
        # ----------------------------------------------------------

        if not self.belt_started:

            self.belt_started = True

            self.belt_start_time = time.time()

            self.get_logger().info(
                "Primera salchicha detectada."
            )

            self.get_logger().info(
                f"Starting conveyor at {self.BELT_SPEED:.2f} m/s"
            )

            # Igual que _set_belt() del ejercicio de paletizado.
            self.set_belt(self.BELT_SPEED)

            return


        # ----------------------------------------------------------
        # COMPROBAR TIEMPO
        # ----------------------------------------------------------

        if self.belt_started and not self.belt_stopped:

            elapsed = (
                time.time() - self.belt_start_time
            )


            # ------------------------------------------------------
            # TODAVÍA DEBE MOVERSE
            # ------------------------------------------------------

            if elapsed < self.STOP_TIME:
                return


            # ------------------------------------------------------
            # PARAR LA CINTA
            # ------------------------------------------------------

            self.belt_stopped = True

            self.set_belt(0.0)

            self.get_logger().info(
                f"Conveyor stopped after {self.STOP_TIME:.1f} seconds."
            )


    # ==============================================================
    # SPAWN DE SALCHICHAS
    # ==============================================================

    def spawn_all_sausages(self):

        NUM_SAUSAGES = self.NUM_SAUSAGES

        MIN_X = -0.18
        MAX_X = 0.18

        MIN_DISTANCE = 0.08


        # ==========================================================
        # GENERAR POSICIONES X ALEATORIAS
        # ==========================================================

        positions = []


        while len(positions) < NUM_SAUSAGES:

            x = random.uniform(
                MIN_X,
                MAX_X
            )

            valid = True


            for p in positions:

                if abs(x - p) < MIN_DISTANCE:

                    valid = False

                    break


            if valid:

                positions.append(x)


        # ==========================================================
        # GENERAR ORDEN DE APARICIÓN ALEATORIO
        # ==========================================================

        spawn_times = sorted(
            random.uniform(0.0, 2.0)
            for _ in range(NUM_SAUSAGES)
        )


        # ==========================================================
        # MEZCLAR LOS NOMBRES
        # ==========================================================

        box_names = [
            f"box_{i}"
            for i in range(NUM_SAUSAGES)
        ]

        random.shuffle(box_names)


        # ==========================================================
        # SPAWN
        # ==========================================================

        start_time = time.time()


        for i, x in enumerate(positions):

            # Esperar hasta el instante correspondiente.
            target_time = (
                start_time +
                spawn_times[i]
            )


            while time.time() < target_time:

                time.sleep(0.005)


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
                "0.58",

                "-z",
                "0.76",

                "-R",
                "0",

                "-P",
                "0",

                "-Y",
                str(yaw),

                "-file",
                "/home/ws/src/CustomRobots/conveyor_belt/sausage.sdf",
            ]


            result = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True
            )


            # ======================================================
            # COMPROBAR SPAWN
            # ======================================================

            if result.returncode != 0:

                self.get_logger().error(
                    f"Failed to spawn {name}: "
                    f"{result.stderr.strip()}"
                )

                continue


            # ======================================================
            # SALCHICHA CREADA
            # ======================================================

            self.get_logger().info(
                f"Spawned {name} at "
                f"x={x:.3f}, "
                f"t={spawn_times[i]:.2f}s"
            )


            self.counter += 1


        # ==========================================================
        # PUBLICAR OBJETOS AGARRABLES
        # ==========================================================

        self.publish_graspable_objects()


        self.get_logger().info(
            f"Spawned {NUM_SAUSAGES} sausages "
            f"within the first 2 seconds."
        )


    # ==============================================================
    # DESTRUCCIÓN
    # ==============================================================

    def destroy_node(self):

        # Detener la cinta al salir.
        if hasattr(self, "speed_pub"):

            msg = Float64()

            msg.data = 0.0

            self.speed_pub.publish(msg)


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