#!/usr/bin/env python3

"""
============================================================
 MOVEIT SERVO DEEP DIAGNOSTIC
 UR5 / GAZEBO HARMONIC / ROS 2
============================================================

Este nodo NO controla el robot.

Su objetivo es descubrir por qué MoveIt Servo genera
movimientos articulares extremadamente pequeños.

Cadena analizada:

    HAL.ServoForTime()
            |
            v
    /servo_node/delta_twist_cmds
            |
            v
        MOVEIT SERVO
            |
            v
    /joint_trajectory_controller/joint_trajectory
            |
            v
    joint_trajectory_controller
            |
            v
       /joint_states


IMPORTANTE:

El diagnóstico distingue entre:

1. Movimiento producido por MoveAbsJ()
2. Movimiento producido posteriormente por ServoForTime()

Esto es importante porque el movimiento inicial hacia HOME
no debe confundirse con el movimiento generado por Servo.


NUEVAS COMPROBACIONES:

- Frame del Twist
- Frecuencia del Twist
- Duración real de recepción de comandos
- Posición del robot antes de Servo
- Posición del robot después de Servo
- Cambio individual por articulación
- Cambio máximo entre trayectorias consecutivas
- Cambio medio entre trayectorias consecutivas
- Cambio acumulado de Servo
- Velocidades articulares generadas
- Trayectorias repetidas o casi idénticas
- Posición deseada del controlador
- Posición real del controlador
- Error entre desired y actual
- Parámetros disponibles de /servo_node
- Detección automática de posibles problemas
"""

import rclpy

from rclpy.node import Node

from rclpy.qos import (
    QoSProfile,
    ReliabilityPolicy,
    HistoryPolicy
)

from sensor_msgs.msg import JointState
from geometry_msgs.msg import TwistStamped
from control_msgs.msg import JointJog
from trajectory_msgs.msg import JointTrajectory
from control_msgs.msg import JointTrajectoryControllerState

import time
import math
import subprocess

from collections import deque


# ============================================================
# CONFIGURACIÓN
# ============================================================

DIAGNOSTIC_DURATION = 60.0


EXPECTED_JOINTS = [
    "shoulder_pan_joint",
    "shoulder_lift_joint",
    "elbow_joint",
    "wrist_1_joint",
    "wrist_2_joint",
    "wrist_3_joint",
]


# Tolerancias

TRAJECTORY_IDENTICAL_THRESHOLD = 1e-8

VERY_SMALL_MOVEMENT_THRESHOLD = 1e-4

SMALL_MOVEMENT_THRESHOLD = 1e-3

SIGNIFICANT_MOVEMENT_THRESHOLD = 1e-2


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def vector_difference(a, b):

    result = []

    size = min(len(a), len(b))

    for i in range(size):

        result.append(
            a[i] - b[i]
        )

    return result


def vector_abs_max(values):

    if len(values) == 0:
        return 0.0

    return max(
        abs(v)
        for v in values
    )


def vector_norm(values):

    return math.sqrt(
        sum(
            v * v
            for v in values
        )
    )


def format_vector(values, precision=8):

    return "[" + ", ".join(
        f"{v:.{precision}f}"
        for v in values
    ) + "]"


# ============================================================
# NODO
# ============================================================

class ServoDeepDiagnostic(Node):

    def __init__(self):

        super().__init__(
            "servo_deep_diagnostic"
        )

        # ----------------------------------------------------
        # QoS
        # ----------------------------------------------------

        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=50
        )

        reliable_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=100
        )

        # ----------------------------------------------------
        # TIEMPO
        # ----------------------------------------------------

        self.start_time = time.time()

        # ----------------------------------------------------
        # JOINT STATES
        # ----------------------------------------------------

        self.joint_state_count = 0

        self.last_joint_positions = None

        self.last_joint_names = None

        self.joint_state_times = deque(
            maxlen=1000
        )

        # ----------------------------------------------------
        # POSICIÓN ANTES DE SERVO
        # ----------------------------------------------------

        self.servo_start_positions = None

        self.servo_start_joint_names = None

        self.servo_end_positions = None

        # ----------------------------------------------------
        # TWIST
        # ----------------------------------------------------

        self.twist_count = 0

        self.first_twist_time = None

        self.last_twist_time = None

        self.last_twist = None

        self.twist_times = deque(
            maxlen=2000
        )

        self.twist_frames = set()

        self.twist_linear_values = []

        self.twist_angular_values = []

        # ----------------------------------------------------
        # JOINT JOG
        # ----------------------------------------------------

        self.joint_jog_count = 0

        # ----------------------------------------------------
        # TRAYECTORIAS
        # ----------------------------------------------------

        self.trajectory_count = 0

        self.first_trajectory_time = None

        self.last_trajectory_time = None

        self.last_trajectory_positions = None

        self.last_trajectory_velocities = None

        self.first_trajectory_positions = None

        self.trajectory_joint_names = None

        # Cambios entre trayectorias consecutivas

        self.trajectory_step_max = 0.0

        self.trajectory_step_sum = 0.0

        self.trajectory_step_count = 0

        self.identical_trajectory_count = 0

        # Cambio total desde primera trayectoria

        self.max_total_trajectory_change = 0.0

        # Movimiento individual por joint

        self.max_trajectory_joint_change = {
            joint: 0.0
            for joint in EXPECTED_JOINTS
        }

        # Velocidades máximas

        self.max_joint_velocity = {
            joint: 0.0
            for joint in EXPECTED_JOINTS
        }

        # ----------------------------------------------------
        # CONTROLLER STATE
        # ----------------------------------------------------

        self.controller_state_count = 0

        self.last_actual_positions = None

        self.last_desired_positions = None

        self.last_error_positions = None

        self.max_controller_error = 0.0

        self.controller_error_sum = 0.0

        self.controller_error_count = 0

        # ----------------------------------------------------
        # FLAGS
        # ----------------------------------------------------

        self.servo_started = False

        # ----------------------------------------------------
        # SUBSCRIBERS
        # ----------------------------------------------------

        self.create_subscription(
            JointState,
            "/joint_states",
            self.joint_state_callback,
            sensor_qos
        )

        self.create_subscription(
            TwistStamped,
            "/servo_node/delta_twist_cmds",
            self.twist_callback,
            reliable_qos
        )

        self.create_subscription(
            JointJog,
            "/servo_node/delta_joint_cmds",
            self.joint_jog_callback,
            reliable_qos
        )

        self.create_subscription(
            JointTrajectory,
            "/joint_trajectory_controller/joint_trajectory",
            self.trajectory_callback,
            reliable_qos
        )

        self.create_subscription(
            JointTrajectoryControllerState,
            "/joint_trajectory_controller/state",
            self.controller_state_callback,
            reliable_qos
        )

        # ----------------------------------------------------
        # TIMER
        # ----------------------------------------------------

        self.create_timer(
            2.0,
            self.print_live_status
        )

        # ----------------------------------------------------
        # INICIO
        # ----------------------------------------------------

        self.get_logger().info("")
        self.get_logger().info(
            "=================================================="
        )
        self.get_logger().info(
            "MOVEIT SERVO DEEP DIAGNOSTIC STARTED"
        )
        self.get_logger().info(
            "=================================================="
        )

        self.get_logger().info(
            f"Duration: {DIAGNOSTIC_DURATION} seconds"
        )

        self.get_logger().info(
            "Execute your HAL program now."
        )

        self.get_logger().info(
            "The node will automatically separate HOME movement"
        )

        self.get_logger().info(
            "from Servo movement."
        )

        self.get_logger().info(
            "=================================================="
        )


    # ========================================================
    # JOINT STATES
    # ========================================================

    def joint_state_callback(self, msg):

        now = time.time()

        self.joint_state_count += 1

        self.joint_state_times.append(
            now
        )

        positions = list(
            msg.position
        )

        names = list(
            msg.name
        )

        self.last_joint_positions = positions

        self.last_joint_names = names

        # ------------------------------------------------
        # PRIMER TWIST = INICIO DE SERVO
        # ------------------------------------------------

        if (
            self.servo_started
            and self.servo_start_positions is not None
        ):

            self.servo_end_positions = positions


    # ========================================================
    # TWIST
    # ========================================================

    def twist_callback(self, msg):

        now = time.time()

        self.twist_count += 1

        self.last_twist = msg

        self.twist_times.append(
            now
        )

        self.last_twist_time = now

        # ------------------------------------------------
        # PRIMER TWIST
        # ------------------------------------------------

        if self.first_twist_time is None:

            self.first_twist_time = now

            self.servo_started = True

            # Guardamos posición justo antes de Servo

            if self.last_joint_positions is not None:

                self.servo_start_positions = list(
                    self.last_joint_positions
                )

                self.servo_start_joint_names = list(
                    self.last_joint_names
                )

            self.get_logger().info("")
            self.get_logger().info(
                "=========================================="
            )
            self.get_logger().info(
                "[SERVO START DETECTED]"
            )
            self.get_logger().info(
                "=========================================="
            )

            if self.servo_start_positions is not None:

                self.get_logger().info(
                    "Robot position captured before Servo:"
                )

                self.get_logger().info(
                    format_vector(
                        self.servo_start_positions,
                        6
                    )
                )

        # ------------------------------------------------
        # FRAME
        # ------------------------------------------------

        frame = msg.header.frame_id

        if frame:
            self.twist_frames.add(
                frame
            )

        # ------------------------------------------------
        # MAGNITUD
        # ------------------------------------------------

        linear = msg.twist.linear

        angular = msg.twist.angular

        linear_norm = math.sqrt(
            linear.x ** 2 +
            linear.y ** 2 +
            linear.z ** 2
        )

        angular_norm = math.sqrt(
            angular.x ** 2 +
            angular.y ** 2 +
            angular.z ** 2
        )

        self.twist_linear_values.append(
            linear_norm
        )

        self.twist_angular_values.append(
            angular_norm
        )

        # ------------------------------------------------
        # PRIMEROS MENSAJES
        # ------------------------------------------------

        if self.twist_count <= 3:

            self.get_logger().info(
                "[TWIST INPUT]"
            )

            self.get_logger().info(
                f"Frame: '{frame}'"
            )

            self.get_logger().info(
                "Linear: "
                f"[{linear.x:.8f}, "
                f"{linear.y:.8f}, "
                f"{linear.z:.8f}]"
            )

            self.get_logger().info(
                "Angular: "
                f"[{angular.x:.8f}, "
                f"{angular.y:.8f}, "
                f"{angular.z:.8f}]"
            )


    # ========================================================
    # JOINT JOG
    # ========================================================

    def joint_jog_callback(self, msg):

        self.joint_jog_count += 1


    # ========================================================
    # TRAYECTORIAS
    # ========================================================

    def trajectory_callback(self, msg):

        now = time.time()

        self.trajectory_count += 1

        self.last_trajectory_time = now

        # ------------------------------------------------
        # PRIMERA TRAYECTORIA
        # ------------------------------------------------

        if self.first_trajectory_time is None:

            self.first_trajectory_time = now

            self.get_logger().info(
                "[SERVO OUTPUT] First trajectory detected"
            )

        # ------------------------------------------------
        # VALIDAR
        # ------------------------------------------------

        if len(msg.points) == 0:
            return

        positions = list(
            msg.points[0].positions
        )

        velocities = list(
            msg.points[0].velocities
        )

        joint_names = list(
            msg.joint_names
        )

        if len(joint_names) == 0:
            return

        # ------------------------------------------------
        # GUARDAR PRIMERA
        # ------------------------------------------------

        if self.first_trajectory_positions is None:

            self.first_trajectory_positions = list(
                positions
            )

            self.trajectory_joint_names = list(
                joint_names
            )

        # ------------------------------------------------
        # CAMBIO ENTRE TRAYECTORIAS
        # ------------------------------------------------

        if self.last_trajectory_positions is not None:

            differences = vector_difference(
                positions,
                self.last_trajectory_positions
            )

            step_max = vector_abs_max(
                differences
            )

            self.trajectory_step_max = max(
                self.trajectory_step_max,
                step_max
            )

            self.trajectory_step_sum += step_max

            self.trajectory_step_count += 1

            if step_max < TRAJECTORY_IDENTICAL_THRESHOLD:

                self.identical_trajectory_count += 1

        # ------------------------------------------------
        # CAMBIO TOTAL
        # ------------------------------------------------

        if self.first_trajectory_positions is not None:

            total_differences = vector_difference(
                positions,
                self.first_trajectory_positions
            )

            total_max = vector_abs_max(
                total_differences
            )

            self.max_total_trajectory_change = max(
                self.max_total_trajectory_change,
                total_max
            )

        # ------------------------------------------------
        # CAMBIO POR JOINT
        # ------------------------------------------------

        for i, joint in enumerate(joint_names):

            if i >= len(positions):
                continue

            if joint not in EXPECTED_JOINTS:
                continue

            if self.first_trajectory_positions is None:
                continue

            if i >= len(
                self.first_trajectory_positions
            ):
                continue

            difference = abs(
                positions[i]
                -
                self.first_trajectory_positions[i]
            )

            self.max_trajectory_joint_change[joint] = max(
                self.max_trajectory_joint_change[joint],
                difference
            )

        # ------------------------------------------------
        # VELOCIDADES
        # ------------------------------------------------

        for i, joint in enumerate(joint_names):

            if joint not in EXPECTED_JOINTS:
                continue

            if i >= len(velocities):
                continue

            velocity = abs(
                velocities[i]
            )

            self.max_joint_velocity[joint] = max(
                self.max_joint_velocity[joint],
                velocity
            )

        # ------------------------------------------------
        # GUARDAR
        # ------------------------------------------------

        self.last_trajectory_positions = positions

        self.last_trajectory_velocities = velocities


    # ========================================================
    # CONTROLLER STATE
    # ========================================================

    def controller_state_callback(self, msg):

        self.controller_state_count += 1

        try:

            actual = list(
                msg.actual.positions
            )

            desired = list(
                msg.desired.positions
            )

            error = list(
                msg.error.positions
            )

            self.last_actual_positions = actual

            self.last_desired_positions = desired

            self.last_error_positions = error

            # ------------------------------------------------
            # ERROR
            # ------------------------------------------------

            if len(error) > 0:

                max_error = vector_abs_max(
                    error
                )

                self.max_controller_error = max(
                    self.max_controller_error,
                    max_error
                )

                self.controller_error_sum += max_error

                self.controller_error_count += 1

        except Exception:
            pass


    # ========================================================
    # FRECUENCIA
    # ========================================================

    def calculate_frequency(self, times):

        if len(times) < 2:

            return 0.0

        elapsed = (
            times[-1]
            -
            times[0]
        )

        if elapsed <= 0:

            return 0.0

        return (
            len(times) - 1
        ) / elapsed


    # ========================================================
    # LIVE STATUS
    # ========================================================

    def print_live_status(self):

        elapsed = (
            time.time()
            -
            self.start_time
        )

        joint_frequency = self.calculate_frequency(
            self.joint_state_times
        )

        twist_frequency = self.calculate_frequency(
            self.twist_times
        )

        self.get_logger().info("")
        self.get_logger().info(
            "------------------------------------------"
        )

        self.get_logger().info(
            f"TIME: {elapsed:.1f} / "
            f"{DIAGNOSTIC_DURATION:.1f} s"
        )

        self.get_logger().info(
            f"joint_states: {self.joint_state_count} "
            f"({joint_frequency:.1f} Hz)"
        )

        self.get_logger().info(
            f"Twist: {self.twist_count} "
            f"({twist_frequency:.1f} Hz)"
        )

        self.get_logger().info(
            f"JointJog: {self.joint_jog_count}"
        )

        self.get_logger().info(
            f"Trajectories: {self.trajectory_count}"
        )

        self.get_logger().info(
            f"Controller states: "
            f"{self.controller_state_count}"
        )

        self.get_logger().info(
            f"Max trajectory step: "
            f"{self.trajectory_step_max:.10f} rad"
        )

        self.get_logger().info(
            f"Max total trajectory change: "
            f"{self.max_total_trajectory_change:.10f} rad"
        )


    # ========================================================
    # EJECUTAR COMANDO
    # ========================================================

    def run_command(self, command):

        try:

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )

            output = result.stdout.strip()

            if result.stderr.strip():

                output += (
                    "\nSTDERR:\n"
                    +
                    result.stderr.strip()
                )

            return output

        except Exception as e:

            return f"ERROR: {e}"


    # ========================================================
    # PARÁMETROS DE SERVO
    # ========================================================

    def check_servo_parameters(self):

        self.get_logger().info("")
        self.get_logger().info(
            "=================================================="
        )
        self.get_logger().info(
            "MOVEIT SERVO PARAMETER CHECK"
        )
        self.get_logger().info(
            "=================================================="
        )

        output = self.run_command(
            "ros2 param list /servo_node"
        )

        if (
            output == ""
            or output.startswith("ERROR")
        ):

            self.get_logger().warn(
                "Could not obtain Servo parameters"
            )

            return

        parameters = output.splitlines()

        self.get_logger().info(
            f"Parameters found: {len(parameters)}"
        )

        interesting_words = [

            "scale",

            "linear",

            "angular",

            "singularity",

            "joint_limit",

            "collision",

            "publish_period",

            "incoming_command_timeout",

            "command_in_type",

            "planning_frame",

            "robot_link_command_frame",

            "move_group",

            "status"
        ]

        interesting_parameters = []

        for parameter in parameters:

            parameter_lower = parameter.lower()

            for word in interesting_words:

                if word in parameter_lower:

                    interesting_parameters.append(
                        parameter
                    )

                    break

        if len(interesting_parameters) == 0:

            self.get_logger().warn(
                "No obvious scaling parameters found"
            )

        else:

            for parameter in interesting_parameters:

                value = self.run_command(
                    f"ros2 param get "
                    f"/servo_node "
                    f"'{parameter}'"
                )

                self.get_logger().info(
                    f"{parameter}: {value}"
                )


    # ========================================================
    # ROS GRAPH
    # ========================================================

    def check_ros_graph(self):

        self.get_logger().info("")
        self.get_logger().info(
            "=================================================="
        )
        self.get_logger().info(
            "IMPORTANT ROS TOPICS"
        )
        self.get_logger().info(
            "=================================================="
        )

        topics = self.run_command(
            "ros2 topic list"
        ).splitlines()

        important_topics = [

            "/joint_states",

            "/servo_node/delta_twist_cmds",

            "/servo_node/delta_joint_cmds",

            "/joint_trajectory_controller/joint_trajectory",

            "/joint_trajectory_controller/state",

            "/servo_node/status"
        ]

        for topic in important_topics:

            if topic in topics:

                self.get_logger().info(
                    f"[OK] {topic}"
                )

            else:

                self.get_logger().warn(
                    f"[MISSING] {topic}"
                )


    # ========================================================
    # MOVIMIENTO REAL DE SERVO
    # ========================================================

    def calculate_real_servo_movement(self):

        if (
            self.servo_start_positions is None
            or self.servo_end_positions is None
        ):

            return None

        differences = vector_difference(
            self.servo_end_positions,
            self.servo_start_positions
        )

        return differences


    # ========================================================
    # REPORTE FINAL
    # ========================================================

    def print_final_report(self):

        self.get_logger().info("")
        self.get_logger().info(
            "=================================================="
        )
        self.get_logger().info(
            "FINAL MOVEIT SERVO DEEP DIAGNOSTIC"
        )
        self.get_logger().info(
            "=================================================="
        )

        # --------------------------------------------------
        # TWIST
        # --------------------------------------------------

        self.get_logger().info("")
        self.get_logger().info(
            "1. TWIST INPUT ANALYSIS"
        )
        self.get_logger().info(
            "--------------------------------------------------"
        )

        twist_frequency = self.calculate_frequency(
            self.twist_times
        )

        self.get_logger().info(
            f"Total Twist messages: "
            f"{self.twist_count}"
        )

        self.get_logger().info(
            f"Twist frequency: "
            f"{twist_frequency:.4f} Hz"
        )

        if (
            self.first_twist_time is not None
            and self.last_twist_time is not None
        ):

            twist_duration = (
                self.last_twist_time
                -
                self.first_twist_time
            )

            self.get_logger().info(
                f"Twist command duration: "
                f"{twist_duration:.6f} s"
            )

        if len(self.twist_frames) > 0:

            self.get_logger().info(
                f"Twist frame(s): "
                f"{list(self.twist_frames)}"
            )

        if len(self.twist_linear_values) > 0:

            max_linear = max(
                self.twist_linear_values
            )

            avg_linear = sum(
                self.twist_linear_values
            ) / len(
                self.twist_linear_values
            )

            self.get_logger().info(
                f"Maximum linear Twist magnitude: "
                f"{max_linear:.10f}"
            )

            self.get_logger().info(
                f"Average linear Twist magnitude: "
                f"{avg_linear:.10f}"
            )

        # --------------------------------------------------
        # TRAJECTORY ANALYSIS
        # --------------------------------------------------

        self.get_logger().info("")
        self.get_logger().info(
            "2. TRAJECTORY ANALYSIS"
        )
        self.get_logger().info(
            "--------------------------------------------------"
        )

        self.get_logger().info(
            f"Total trajectories: "
            f"{self.trajectory_count}"
        )

        self.get_logger().info(
            f"Maximum step between trajectories: "
            f"{self.trajectory_step_max:.10f} rad"
        )

        if self.trajectory_step_count > 0:

            average_step = (
                self.trajectory_step_sum
                /
                self.trajectory_step_count
            )

            self.get_logger().info(
                f"Average step between trajectories: "
                f"{average_step:.10f} rad"
            )

        else:

            average_step = 0.0

        self.get_logger().info(
            f"Maximum total trajectory change: "
            f"{self.max_total_trajectory_change:.10f} rad"
        )

        self.get_logger().info(
            f"Almost identical trajectories: "
            f"{self.identical_trajectory_count}"
        )

        if self.trajectory_count > 1:

            identical_percentage = (
                100.0
                *
                self.identical_trajectory_count
                /
                (self.trajectory_count - 1)
            )

            self.get_logger().info(
                f"Identical percentage: "
                f"{identical_percentage:.4f}%"
            )

        # --------------------------------------------------
        # MOVIMIENTO POR ARTICULACIÓN
        # --------------------------------------------------

        self.get_logger().info("")
        self.get_logger().info(
            "3. MOVEMENT GENERATED BY EACH JOINT"
        )
        self.get_logger().info(
            "--------------------------------------------------"
        )

        for joint in EXPECTED_JOINTS:

            movement = (
                self.max_trajectory_joint_change[
                    joint
                ]
            )

            self.get_logger().info(
                f"{joint}: "
                f"{movement:.10f} rad "
                f"({math.degrees(movement):.8f} deg)"
            )

        # --------------------------------------------------
        # VELOCIDADES
        # --------------------------------------------------

        self.get_logger().info("")
        self.get_logger().info(
            "4. MAXIMUM GENERATED JOINT VELOCITIES"
        )
        self.get_logger().info(
            "--------------------------------------------------"
        )

        for joint in EXPECTED_JOINTS:

            velocity = (
                self.max_joint_velocity[
                    joint
                ]
            )

            self.get_logger().info(
                f"{joint}: "
                f"{velocity:.10f} rad/s"
            )

        # --------------------------------------------------
        # MOVIMIENTO REAL DURANTE SERVO
        # --------------------------------------------------

        self.get_logger().info("")
        self.get_logger().info(
            "5. REAL MOVEMENT DURING SERVO ONLY"
        )
        self.get_logger().info(
            "--------------------------------------------------"
        )

        real_movement = (
            self.calculate_real_servo_movement()
        )

        real_movement_max = 0.0

        if real_movement is not None:

            real_movement_max = vector_abs_max(
                real_movement
            )

            self.get_logger().info(
                "Joint differences "
                "(after Servo - before Servo):"
            )

            self.get_logger().info(
                format_vector(
                    real_movement,
                    10
                )
            )

            self.get_logger().info(
                f"Maximum real Servo movement: "
                f"{real_movement_max:.10f} rad"
            )

            self.get_logger().info(
                f"Maximum real Servo movement: "
                f"{math.degrees(real_movement_max):.10f} deg"
            )

        else:

            self.get_logger().warn(
                "Could not calculate Servo-only movement"
            )

        # --------------------------------------------------
        # CONTROLLER ERROR
        # --------------------------------------------------

        self.get_logger().info("")
        self.get_logger().info(
            "6. CONTROLLER FOLLOWING ANALYSIS"
        )
        self.get_logger().info(
            "--------------------------------------------------"
        )

        self.get_logger().info(
            f"Controller state messages: "
            f"{self.controller_state_count}"
        )

        self.get_logger().info(
            f"Maximum controller error: "
            f"{self.max_controller_error:.10f} rad"
        )

        if self.controller_error_count > 0:

            average_error = (
                self.controller_error_sum
                /
                self.controller_error_count
            )

            self.get_logger().info(
                f"Average controller error: "
                f"{average_error:.10f} rad"
            )

        # --------------------------------------------------
        # COMPARACIÓN
        # --------------------------------------------------

        self.get_logger().info("")
        self.get_logger().info(
            "7. COMPLETE CHAIN COMPARISON"
        )
        self.get_logger().info(
            "--------------------------------------------------"
        )

        if self.last_twist is not None:

            linear = (
                self.last_twist.twist.linear
            )

            self.get_logger().info(
                "Last Twist:"
            )

            self.get_logger().info(
                f"linear.x = {linear.x:.10f}"
            )

            self.get_logger().info(
                f"linear.y = {linear.y:.10f}"
            )

            self.get_logger().info(
                f"linear.z = {linear.z:.10f}"
            )

        self.get_logger().info(
            f"Trajectory maximum movement: "
            f"{self.max_total_trajectory_change:.10f} rad"
        )

        self.get_logger().info(
            f"Real robot movement: "
            f"{real_movement_max:.10f} rad"
        )

        # --------------------------------------------------
        # ROS GRAPH
        # --------------------------------------------------

        self.check_ros_graph()

        # --------------------------------------------------
        # PARÁMETROS SERVO
        # --------------------------------------------------

        self.check_servo_parameters()

        # --------------------------------------------------
        # CONCLUSIÓN
        # --------------------------------------------------

        self.get_logger().info("")
        self.get_logger().info(
            "=================================================="
        )
        self.get_logger().info(
            "AUTOMATIC DIAGNOSIS"
        )
        self.get_logger().info(
            "=================================================="
        )

        # --------------------------------------------------
        # CASO 1
        # --------------------------------------------------

        if self.twist_count == 0:

            self.get_logger().error(
                "FAIL: HAL is not sending Twist commands"
            )

        # --------------------------------------------------
        # CASO 2
        # --------------------------------------------------

        elif self.trajectory_count == 0:

            self.get_logger().error(
                "FAIL: Servo receives Twist but "
                "does not generate trajectories"
            )

        # --------------------------------------------------
        # CASO 3
        # --------------------------------------------------

        elif (
            self.max_total_trajectory_change
            <
            VERY_SMALL_MOVEMENT_THRESHOLD
        ):

            self.get_logger().error(
                "MAIN PROBLEM DETECTED:"
            )

            self.get_logger().error(
                "MoveIt Servo is generating an "
                "EXTREMELY SMALL joint motion."
            )

            self.get_logger().error(
                f"Maximum generated motion: "
                f"{self.max_total_trajectory_change:.10f} rad"
            )

            self.get_logger().error(
                "The controller is probably NOT the problem."
            )

            self.get_logger().error(
                "Investigate:"
            )

            self.get_logger().error(
                "- Servo velocity scaling"
            )

            self.get_logger().error(
                "- Linear/angular scale"
            )

            self.get_logger().error(
                "- Singularity scaling"
            )

            self.get_logger().error(
                "- Joint limit scaling"
            )

            self.get_logger().error(
                "- Collision scaling"
            )

            self.get_logger().error(
                "- Incorrect command frame"
            )

            self.get_logger().error(
                "- Incorrect planning frame"
            )

            self.get_logger().error(
                "- HAL command interpretation"
            )

        # --------------------------------------------------
        # CASO 4
        # --------------------------------------------------

        elif (
            real_movement_max
            <
            self.max_total_trajectory_change
            *
            0.1
        ):

            self.get_logger().error(
                "PROBLEM DETECTED:"
            )

            self.get_logger().error(
                "Servo generates significant trajectories"
            )

            self.get_logger().error(
                "but the real robot barely follows them."
            )

            self.get_logger().error(
                "Likely problem:"
            )

            self.get_logger().error(
                "joint_trajectory_controller / ros2_control"
            )

        # --------------------------------------------------
        # CASO 5
        # --------------------------------------------------

        elif (
            self.max_controller_error
            >
            0.01
        ):

            self.get_logger().error(
                "PROBLEM DETECTED:"
            )

            self.get_logger().error(
                "The controller is receiving trajectories"
            )

            self.get_logger().error(
                "but cannot accurately follow them."
            )

        # --------------------------------------------------
        # SUCCESS
        # --------------------------------------------------

        else:

            self.get_logger().info(
                "Servo chain appears to be functioning."
            )

            self.get_logger().info(
                "No obvious transmission failure detected."
            )

        self.get_logger().info(
            "=================================================="
        )


# ============================================================
# MAIN
# ============================================================

def main(args=None):

    rclpy.init(args=args)

    node = ServoDeepDiagnostic()

    start = time.time()

    try:

        while rclpy.ok():

            rclpy.spin_once(
                node,
                timeout_sec=0.1
            )

            elapsed = (
                time.time()
                -
                start
            )

            if elapsed >= DIAGNOSTIC_DURATION:

                break

    except KeyboardInterrupt:

        node.get_logger().warn(
            "Diagnostic interrupted"
        )

    finally:

        node.print_final_report()

        node.destroy_node()

        rclpy.shutdown()


if __name__ == "__main__":

    main()