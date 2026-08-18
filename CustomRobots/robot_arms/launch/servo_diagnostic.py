#!/usr/bin/env python3

"""
============================================================
 MOVEIT SERVO / UR5 / GAZEBO HARMONIC
 ADVANCED DIAGNOSTIC TOOL
============================================================

Este nodo NO controla el robot.

Su objetivo es diagnosticar toda la cadena:

    HAL.ServoForTime()
            |
            v
    /servo_node/delta_twist_cmds
            |
            v
        MoveIt Servo
            |
            v
    /joint_trajectory_controller/joint_trajectory
            |
            v
    joint_trajectory_controller
            |
            v
       /joint_states


El diagnóstico diferencia especialmente entre:

OPCIÓN A
--------

Servo genera trayectorias con cambios articulares
muy pequeños.

En este caso:

    Twist              -> OK
    Trajectories       -> OK
    Desired positions  -> Cambian muy poco
    Actual positions   -> Cambian poco o correctamente

El problema estaría relacionado con:

    - command_in_type
    - publish_period
    - scale.linear
    - incoming_command_timeout
    - Servo velocity scaling
    - velocidad cartesiana demasiado pequeña
    - frame de referencia
    - configuración cinemática


OPCIÓN B
--------

Servo genera trayectorias correctas, pero estas no son
ejecutadas correctamente por el controller.

En este caso:

    Twist              -> OK
    Trajectories       -> OK
    Desired positions  -> Cambian
    Actual positions   -> No cambian o no siguen
    Controller error   -> Alto

El problema estaría entre:

    joint_trajectory_controller

y:

    ros2_control
            |
            v
    gz_ros2_control
            |
            v
         Gazebo


IMPORTANTE:

El nodo detecta automáticamente el inicio del Servo.

Todo el movimiento producido antes del primer Twist,
por ejemplo:

    HAL.MoveAbsJ(HOME, ...)

NO se utiliza para evaluar el movimiento producido
por Servo.

============================================================
"""

import math
import time
import subprocess

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

from tf2_ros import (
    Buffer,
    TransformListener
)


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


IMPORTANT_TFS = [

    ("base_link", "tool0"),

]


IMPORTANT_TOPICS = [

    "/joint_states",

    "/servo_node/delta_twist_cmds",

    "/servo_node/delta_joint_cmds",

    "/joint_trajectory_controller/joint_trajectory",

    "/joint_trajectory_controller/state",

]


IMPORTANT_NODES = [

    "/servo_node",

    "/move_group",

    "/controller_manager",

]


IMPORTANT_SERVICES = [

    "/servo_node/start_servo",

    "/servo_node/stop_servo",

]


IMPORTANT_ACTIONS = [

    "/move_action",

    "/joint_trajectory_controller/follow_joint_trajectory",

]


# ============================================================
# UMBRALES
# ============================================================

# Movimiento mínimo para considerar
# que una articulación realmente se ha movido.

REAL_MOVEMENT_THRESHOLD = 0.001


# Cambio entre trayectorias consecutivas.

SMALL_TRAJECTORY_CHANGE = 0.0001

MEDIUM_TRAJECTORY_CHANGE = 0.001

LARGE_TRAJECTORY_CHANGE = 0.01


# Error máximo deseado-real considerado aceptable.

CONTROLLER_ERROR_GOOD = 0.01

CONTROLLER_ERROR_WARNING = 0.05


# ============================================================
# NODO
# ============================================================

class ServoDiagnostic(Node):

    def __init__(self):

        super().__init__(
            "servo_diagnostic"
        )


        # ====================================================
        # QoS
        # ====================================================

        best_effort_qos = QoSProfile(

            reliability=ReliabilityPolicy.BEST_EFFORT,

            history=HistoryPolicy.KEEP_LAST,

            depth=10

        )


        reliable_qos = QoSProfile(

            reliability=ReliabilityPolicy.RELIABLE,

            history=HistoryPolicy.KEEP_LAST,

            depth=10

        )


        # ====================================================
        # TIEMPO
        # ====================================================

        self.start_time = time.time()


        # ====================================================
        # JOINT STATES
        # ====================================================

        self.joint_state_count = 0

        self.first_joint_state = None

        self.last_joint_state = None


        self.expected_joints_found = False


        # Posiciones actuales.

        self.current_joint_positions = {}


        # ====================================================
        # MOVIMIENTO ANTES DE SERVO
        # ====================================================

        # Este movimiento NO se utiliza para evaluar Servo.

        self.initial_positions = {}

        self.max_total_joint_change = 0.0


        # ====================================================
        # INICIO DE SERVO
        # ====================================================

        self.servo_started = False

        self.servo_start_time = None


        # Posiciones articulares justo antes del primer Twist.

        self.servo_initial_positions = {}


        # Máximo movimiento desde que empezó Servo.

        self.servo_max_joint_change = 0.0

        self.servo_joint_changes = {

            joint: 0.0

            for joint in EXPECTED_JOINTS

        }


        # ====================================================
        # TWIST
        # ====================================================

        self.twist_count = 0

        self.first_twist_time = None

        self.last_twist = None


        # ====================================================
        # JOINT JOG
        # ====================================================

        self.joint_jog_count = 0


        # ====================================================
        # TRAYECTORIAS
        # ====================================================

        self.trajectory_count = 0

        self.first_trajectory_time = None


        # Última posición objetivo recibida.

        self.last_trajectory_positions = None


        # Máximo cambio entre trayectorias consecutivas.

        self.max_trajectory_step = 0.0


        # Suma de cambios para obtener promedio.

        self.trajectory_step_sum = 0.0

        self.trajectory_step_count = 0


        # Cambio total desde la primera trayectoria.

        self.first_servo_trajectory_positions = None

        self.max_total_trajectory_change = 0.0


        # ====================================================
        # CONTROLLER
        # ====================================================

        self.controller_state_count = 0


        self.last_actual_positions = None

        self.last_desired_positions = None

        self.last_error_positions = None


        # Posiciones iniciales del controller
        # cuando comienza Servo.

        self.servo_initial_actual_positions = None

        self.servo_initial_desired_positions = None


        # Movimiento de actual.

        self.max_actual_change_during_servo = 0.0


        # Movimiento de desired.

        self.max_desired_change_during_servo = 0.0


        # Error máximo.

        self.max_controller_error = 0.0

        self.controller_error_sum = 0.0

        self.controller_error_count = 0


        # Número de veces que desired cambia.

        self.desired_changed_count = 0


        # Número de veces que actual cambia.

        self.actual_changed_count = 0


        # ====================================================
        # FRECUENCIA
        # ====================================================

        self.joint_state_times = []

        self.max_frequency_samples = 500


        # ====================================================
        # TF
        # ====================================================

        self.tf_buffer = Buffer()

        self.tf_listener = TransformListener(

            self.tf_buffer,

            self

        )


        # ====================================================
        # SUBSCRIBERS
        # ====================================================

        self.create_subscription(

            JointState,

            "/joint_states",

            self.joint_state_callback,

            best_effort_qos

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


        # ====================================================
        # TIMER
        # ====================================================

        self.create_timer(

            1.0,

            self.print_live_status

        )


        # ====================================================
        # INICIO
        # ====================================================

        self.get_logger().info(
            ""
        )

        self.get_logger().info(
            "=================================================="
        )

        self.get_logger().info(
            "ADVANCED MOVEIT SERVO DIAGNOSTIC STARTED"
        )

        self.get_logger().info(
            "=================================================="
        )

        self.get_logger().info(
            f"Diagnostic duration: "
            f"{DIAGNOSTIC_DURATION} seconds"
        )

        self.get_logger().info(
            ""
        )

        self.get_logger().info(
            "IMPORTANT:"
        )

        self.get_logger().info(
            "Movement before the first Servo Twist"
        )

        self.get_logger().info(
            "will NOT be used to evaluate Servo."
        )

        self.get_logger().info(
            ""
        )

        self.get_logger().info(
            "Now execute your HAL program."
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

        self.last_joint_state = msg


        # ----------------------------------------------------
        # FRECUENCIA
        # ----------------------------------------------------

        self.joint_state_times.append(now)

        if len(
            self.joint_state_times
        ) > self.max_frequency_samples:

            self.joint_state_times.pop(0)


        # ----------------------------------------------------
        # CONVERTIR A DICCIONARIO
        # ----------------------------------------------------

        positions = {

            name: position

            for name, position in zip(

                msg.name,

                msg.position

            )

        }


        self.current_joint_positions = positions


        # ----------------------------------------------------
        # PRIMER MENSAJE
        # ----------------------------------------------------

        if self.first_joint_state is None:

            self.first_joint_state = msg

            self.initial_positions = positions.copy()


            self.get_logger().info(
                "[JOINT STATES] First message received"
            )


            missing = []


            for joint in EXPECTED_JOINTS:

                if joint not in positions:

                    missing.append(
                        joint
                    )


            if len(missing) == 0:

                self.expected_joints_found = True


                self.get_logger().info(
                    "[JOINT STATES] "
                    "All expected UR joints found"
                )

            else:

                self.get_logger().warn(
                    f"[JOINT STATES] "
                    f"Missing joints: {missing}"
                )


        # ----------------------------------------------------
        # MOVIMIENTO TOTAL
        # ----------------------------------------------------

        for joint in EXPECTED_JOINTS:

            if (
                joint in positions
                and
                joint in self.initial_positions
            ):

                difference = abs(

                    positions[joint]

                    -

                    self.initial_positions[joint]

                )


                if difference > self.max_total_joint_change:

                    self.max_total_joint_change = difference


        # ----------------------------------------------------
        # MOVIMIENTO DURANTE SERVO
        # ----------------------------------------------------

        if self.servo_started:

            for joint in EXPECTED_JOINTS:

                if (

                    joint in positions

                    and

                    joint in self.servo_initial_positions

                ):

                    difference = abs(

                        positions[joint]

                        -

                        self.servo_initial_positions[
                            joint
                        ]

                    )


                    if difference > self.servo_joint_changes[
                        joint
                    ]:

                        self.servo_joint_changes[
                            joint
                        ] = difference


                    if difference > self.servo_max_joint_change:

                        self.servo_max_joint_change = difference


    # ========================================================
    # TWIST CALLBACK
    # ========================================================

    def twist_callback(self, msg):

        self.twist_count += 1

        self.last_twist = msg


        # ----------------------------------------------------
        # DETECTAR INICIO DE SERVO
        # ----------------------------------------------------

        if not self.servo_started:

            self.servo_started = True

            self.servo_start_time = time.time()


            # Guardamos las posiciones JUSTO antes
            # de empezar Servo.

            self.servo_initial_positions = (

                self.current_joint_positions.copy()

            )


            self.get_logger().info(
                ""
            )

            self.get_logger().info(
                "=================================================="
            )

            self.get_logger().info(
                "[SERVO START DETECTED]"
            )

            self.get_logger().info(
                "From this moment, movement is measured"
            )

            self.get_logger().info(
                "ONLY for Servo."
            )

            self.get_logger().info(
                ""
            )

            self.get_logger().info(
                "Servo initial joint positions:"
            )

            for joint in EXPECTED_JOINTS:

                if joint in self.servo_initial_positions:

                    self.get_logger().info(

                        f"  {joint}: "

                        f"{self.servo_initial_positions[joint]:.6f}"

                    )


            self.get_logger().info(
                "=================================================="
            )


        # ----------------------------------------------------
        # PRIMER TWIST
        # ----------------------------------------------------

        if self.first_twist_time is None:

            self.first_twist_time = time.time()


            self.get_logger().info(
                "[SERVO INPUT] "
                "First Twist command received"
            )


        # ----------------------------------------------------
        # MOSTRAR PRIMEROS COMANDOS
        # ----------------------------------------------------

        if self.twist_count <= 3:

            linear = msg.twist.linear

            angular = msg.twist.angular


            self.get_logger().info(
                "[SERVO INPUT] Twist:"
            )

            self.get_logger().info(

                f"  linear: "

                f"[{linear.x:.6f}, "

                f"{linear.y:.6f}, "

                f"{linear.z:.6f}]"

            )

            self.get_logger().info(

                f"  angular: "

                f"[{angular.x:.6f}, "

                f"{angular.y:.6f}, "

                f"{angular.z:.6f}]"

            )


    # ========================================================
    # JOINT JOG
    # ========================================================

    def joint_jog_callback(self, msg):

        self.joint_jog_count += 1


        if self.joint_jog_count == 1:

            self.get_logger().info(
                "[SERVO INPUT] "
                "JointJog commands detected"
            )


    # ========================================================
    # TRAJECTORY
    # ========================================================

    def trajectory_callback(self, msg):

        self.trajectory_count += 1


        # ----------------------------------------------------
        # PRIMERA TRAYECTORIA
        # ----------------------------------------------------

        if self.first_trajectory_time is None:

            self.first_trajectory_time = time.time()


            self.get_logger().info(
                "[SERVO OUTPUT] "
                "First JointTrajectory received"
            )


        # ----------------------------------------------------
        # COMPROBAR QUE EXISTEN PUNTOS
        # ----------------------------------------------------

        if len(msg.points) == 0:

            return


        positions = list(

            msg.points[0].positions

        )


        # ----------------------------------------------------
        # PRIMERA TRAYECTORIA
        # ----------------------------------------------------

        if self.first_servo_trajectory_positions is None:

            self.first_servo_trajectory_positions = (

                positions.copy()

            )


            self.get_logger().info(
                "[SERVO OUTPUT] "
                "First trajectory joint positions:"
            )

            for name, position in zip(

                msg.joint_names,

                positions

            ):

                self.get_logger().info(

                    f"  {name}: "

                    f"{position:.8f}"

                )


        # ----------------------------------------------------
        # CAMBIO ENTRE TRAYECTORIAS
        # ----------------------------------------------------

        if (

            self.last_trajectory_positions is not None

            and

            len(
                self.last_trajectory_positions
            ) == len(positions)

        ):

            max_step = 0.0


            for current, previous in zip(

                positions,

                self.last_trajectory_positions

            ):

                difference = abs(

                    current

                    -

                    previous

                )


                if difference > max_step:

                    max_step = difference


            self.trajectory_step_count += 1

            self.trajectory_step_sum += max_step


            if max_step > self.max_trajectory_step:

                self.max_trajectory_step = max_step


        # ----------------------------------------------------
        # CAMBIO TOTAL DESDE LA PRIMERA
        # ----------------------------------------------------

        if (

            self.first_servo_trajectory_positions

            is not None

        ):

            for current, initial in zip(

                positions,

                self.first_servo_trajectory_positions

            ):

                difference = abs(

                    current

                    -

                    initial

                )


                if difference > (

                    self.max_total_trajectory_change

                ):

                    self.max_total_trajectory_change = (

                        difference

                    )


        # ----------------------------------------------------
        # GUARDAR
        # ----------------------------------------------------

        self.last_trajectory_positions = (

            positions.copy()

        )


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


        except Exception as e:

            self.get_logger().warn(

                f"Error reading controller state: {e}"

            )

            return


        # ----------------------------------------------------
        # GUARDAR
        # ----------------------------------------------------

        self.last_actual_positions = actual

        self.last_desired_positions = desired

        self.last_error_positions = error


        # ----------------------------------------------------
        # SOLO ANALIZAMOS SERVO DESPUÉS DE SU INICIO
        # ----------------------------------------------------

        if not self.servo_started:

            return


        # ----------------------------------------------------
        # POSICIONES INICIALES
        # ----------------------------------------------------

        if self.servo_initial_actual_positions is None:

            self.servo_initial_actual_positions = (

                actual.copy()

            )


        if self.servo_initial_desired_positions is None:

            self.servo_initial_desired_positions = (

                desired.copy()

            )


        # ----------------------------------------------------
        # CAMBIO DE ACTUAL
        # ----------------------------------------------------

        if (

            len(actual)

            ==

            len(
                self.servo_initial_actual_positions
            )

        ):

            max_change = 0.0


            for current, initial in zip(

                actual,

                self.servo_initial_actual_positions

            ):

                difference = abs(

                    current

                    -

                    initial

                )


                if difference > max_change:

                    max_change = difference


            if max_change > self.max_actual_change_during_servo:

                self.max_actual_change_during_servo = (

                    max_change

                )


            if max_change > REAL_MOVEMENT_THRESHOLD:

                self.actual_changed_count += 1


        # ----------------------------------------------------
        # CAMBIO DE DESIRED
        # ----------------------------------------------------

        if (

            len(desired)

            ==

            len(
                self.servo_initial_desired_positions
            )

        ):

            max_change = 0.0


            for current, initial in zip(

                desired,

                self.servo_initial_desired_positions

            ):

                difference = abs(

                    current

                    -

                    initial

                )


                if difference > max_change:

                    max_change = difference


            if max_change > self.max_desired_change_during_servo:

                self.max_desired_change_during_servo = (

                    max_change

                )


            if max_change > REAL_MOVEMENT_THRESHOLD:

                self.desired_changed_count += 1


        # ----------------------------------------------------
        # ERROR DEL CONTROLLER
        # ----------------------------------------------------

        for value in error:

            absolute_error = abs(value)


            self.controller_error_sum += (

                absolute_error

            )


            self.controller_error_count += 1


            if absolute_error > self.max_controller_error:

                self.max_controller_error = (

                    absolute_error

                )


    # ========================================================
    # FRECUENCIA
    # ========================================================

    def get_joint_state_frequency(self):

        if len(self.joint_state_times) < 2:

            return 0.0


        elapsed = (

            self.joint_state_times[-1]

            -

            self.joint_state_times[0]

        )


        if elapsed <= 0:

            return 0.0


        return (

            len(self.joint_state_times) - 1

        ) / elapsed


    # ========================================================
    # PROMEDIO CAMBIO DE TRAYECTORIA
    # ========================================================

    def get_average_trajectory_step(self):

        if self.trajectory_step_count == 0:

            return 0.0


        return (

            self.trajectory_step_sum

            /

            self.trajectory_step_count

        )


    # ========================================================
    # ERROR MEDIO
    # ========================================================

    def get_average_controller_error(self):

        if self.controller_error_count == 0:

            return 0.0


        return (

            self.controller_error_sum

            /

            self.controller_error_count

        )


    # ========================================================
    # ESTADO EN VIVO
    # ========================================================

    def print_live_status(self):

        elapsed = (

            time.time()

            -

            self.start_time

        )


        frequency = (

            self.get_joint_state_frequency()

        )


        self.get_logger().info(
            ""
        )

        self.get_logger().info(
            "------------------------------------------"
        )

        self.get_logger().info(

            f"TIME: {elapsed:.1f} / "

            f"{DIAGNOSTIC_DURATION:.1f} s"

        )


        self.get_logger().info(

            f"Servo started: "

            f"{self.servo_started}"

        )


        self.get_logger().info(

            f"joint_states: "

            f"{self.joint_state_count} "

            f"({frequency:.1f} Hz)"

        )


        self.get_logger().info(

            f"Twist commands: "

            f"{self.twist_count}"

        )


        self.get_logger().info(

            f"Trajectories: "

            f"{self.trajectory_count}"

        )


        self.get_logger().info(

            f"Controller states: "

            f"{self.controller_state_count}"

        )


        if self.servo_started:

            self.get_logger().info(
                ""
            )

            self.get_logger().info(
                "SERVO-ONLY MEASUREMENTS:"
            )


            self.get_logger().info(

                f"Max trajectory step: "

                f"{self.max_trajectory_step:.8f} rad"

            )


            self.get_logger().info(

                f"Average trajectory step: "

                f"{self.get_average_trajectory_step():.8f} rad"

            )


            self.get_logger().info(

                f"Total trajectory change: "

                f"{self.max_total_trajectory_change:.8f} rad"

            )


            self.get_logger().info(

                f"Desired movement: "

                f"{self.max_desired_change_during_servo:.8f} rad"

            )


            self.get_logger().info(

                f"Actual movement: "

                f"{self.max_actual_change_during_servo:.8f} rad"

            )


            self.get_logger().info(

                f"Max controller error: "

                f"{self.max_controller_error:.8f} rad"

            )


    # ========================================================
    # TF CHECK
    # ========================================================

    def check_tf(self):

        results = []


        for source, target in IMPORTANT_TFS:

            try:

                transform = (

                    self.tf_buffer.lookup_transform(

                        source,

                        target,

                        rclpy.time.Time()

                    )

                )


                results.append(

                    (

                        source,

                        target,

                        True,

                        transform

                    )

                )


            except Exception as e:

                results.append(

                    (

                        source,

                        target,

                        False,

                        str(e)

                    )

                )


        return results


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


            return result.stdout.strip()


        except Exception as e:

            return f"ERROR: {e}"


    # ========================================================
    # ROS GRAPH
    # ========================================================

    def check_ros_graph(self):

        nodes_output = self.run_command(

            "ros2 node list"

        )


        topics_output = self.run_command(

            "ros2 topic list"

        )


        services_output = self.run_command(

            "ros2 service list"

        )


        actions_output = self.run_command(

            "ros2 action list"

        )


        return {

            "nodes":

                nodes_output.splitlines(),


            "topics":

                topics_output.splitlines(),


            "services":

                services_output.splitlines(),


            "actions":

                actions_output.splitlines(),

        }


    # ========================================================
    # REPORTE FINAL
    # ========================================================

    def print_final_report(self):

        self.get_logger().info(
            ""
        )

        self.get_logger().info(
            "=================================================="
        )

        self.get_logger().info(
            "FINAL ADVANCED DIAGNOSTIC REPORT"
        )

        self.get_logger().info(
            "=================================================="
        )


        # ----------------------------------------------------
        # RESUMEN DE LA CADENA
        # ----------------------------------------------------

        self.get_logger().info(
            ""
        )

        self.get_logger().info(
            "SERVO PIPELINE"
        )

        self.get_logger().info(
            "--------------------------------------------------"
        )


        self.get_logger().info(

            f"Twist messages: "

            f"{self.twist_count}"

        )


        self.get_logger().info(

            f"Generated trajectories: "

            f"{self.trajectory_count}"

        )


        self.get_logger().info(

            f"Controller state messages: "

            f"{self.controller_state_count}"

        )


        # ----------------------------------------------------
        # MOVIMIENTO POR ARTICULACIÓN
        # ----------------------------------------------------

        self.get_logger().info(
            ""
        )

        self.get_logger().info(
            "REAL MOVEMENT DURING SERVO"
        )

        self.get_logger().info(
            "--------------------------------------------------"
        )


        for joint in EXPECTED_JOINTS:

            change = (

                self.servo_joint_changes.get(

                    joint,

                    0.0

                )

            )


            self.get_logger().info(

                f"{joint}: "

                f"{change:.8f} rad"

            )


        # ----------------------------------------------------
        # TRAYECTORIAS
        # ----------------------------------------------------

        self.get_logger().info(
            ""
        )

        self.get_logger().info(
            "TRAJECTORY ANALYSIS"
        )

        self.get_logger().info(
            "--------------------------------------------------"
        )


        self.get_logger().info(

            f"Maximum step between trajectories: "

            f"{self.max_trajectory_step:.10f} rad"

        )


        self.get_logger().info(

            f"Average step between trajectories: "

            f"{self.get_average_trajectory_step():.10f} rad"

        )


        self.get_logger().info(

            f"Maximum total trajectory change: "

            f"{self.max_total_trajectory_change:.10f} rad"

        )


        # ----------------------------------------------------
        # CONTROLLER
        # ----------------------------------------------------

        self.get_logger().info(
            ""
        )

        self.get_logger().info(
            "CONTROLLER ANALYSIS"
        )

        self.get_logger().info(
            "--------------------------------------------------"
        )


        self.get_logger().info(

            f"Desired movement: "

            f"{self.max_desired_change_during_servo:.10f} rad"

        )


        self.get_logger().info(

            f"Actual movement: "

            f"{self.max_actual_change_during_servo:.10f} rad"

        )


        self.get_logger().info(

            f"Maximum controller error: "

            f"{self.max_controller_error:.10f} rad"

        )


        self.get_logger().info(

            f"Average controller error: "

            f"{self.get_average_controller_error():.10f} rad"

        )


        # ----------------------------------------------------
        # MOVIMIENTO REAL
        # ----------------------------------------------------

        self.get_logger().info(
            ""
        )

        self.get_logger().info(
            "MOVEMENT RESULT"
        )

        self.get_logger().info(
            "--------------------------------------------------"
        )


        if (

            self.servo_max_joint_change

            >

            REAL_MOVEMENT_THRESHOLD

        ):

            self.get_logger().info(

                "[OK] Robot moved during Servo"

            )


        else:

            self.get_logger().error(

                "[FAIL] Robot did NOT move significantly "

                "during Servo"

            )


        # ----------------------------------------------------
        # TF
        # ----------------------------------------------------

        self.get_logger().info(
            ""
        )

        self.get_logger().info(
            "TF CHECK"
        )

        self.get_logger().info(
            "--------------------------------------------------"
        )


        tf_results = self.check_tf()


        for source, target, success, data in tf_results:

            if success:

                self.get_logger().info(

                    f"[OK] TF: "

                    f"{source} -> {target}"

                )

            else:

                self.get_logger().error(

                    f"[FAIL] TF missing: "

                    f"{source} -> {target}"

                )


        # ----------------------------------------------------
        # ROS GRAPH
        # ----------------------------------------------------

        self.get_logger().info(
            ""
        )

        self.get_logger().info(
            "ROS GRAPH"
        )

        self.get_logger().info(
            "--------------------------------------------------"
        )


        graph = self.check_ros_graph()


        for node in IMPORTANT_NODES:

            if node in graph["nodes"]:

                self.get_logger().info(

                    f"[OK] Node: {node}"

                )

            else:

                self.get_logger().warn(

                    f"[WARN] Node missing: {node}"

                )


        for topic in IMPORTANT_TOPICS:

            if topic in graph["topics"]:

                self.get_logger().info(

                    f"[OK] Topic: {topic}"

                )

            else:

                self.get_logger().warn(

                    f"[WARN] Topic missing: {topic}"

                )


        # ----------------------------------------------------
        # CONCLUSIÓN AUTOMÁTICA
        # ----------------------------------------------------

        self.get_logger().info(
            ""
        )

        self.get_logger().info(
            "=================================================="
        )

        self.get_logger().info(
            "AUTOMATIC CONCLUSION"
        )

        self.get_logger().info(
            "=================================================="
        )


        # CASO 1
        # ------------------------------------------------

        if self.twist_count == 0:

            self.get_logger().error(
                ""
            )

            self.get_logger().error(
                "PROBLEM 1: NO SERVO INPUT"
            )

            self.get_logger().error(

                "HAL is not publishing Twist commands."

            )


        # CASO 2
        # ------------------------------------------------

        elif self.trajectory_count == 0:

            self.get_logger().error(
                ""
            )

            self.get_logger().error(
                "PROBLEM 2: SERVO DOES NOT GENERATE OUTPUT"
            )

            self.get_logger().error(

                "Twist commands reach Servo, but no "

                "JointTrajectory is generated."

            )


        # CASO 3
        # ------------------------------------------------

        elif (

            self.max_total_trajectory_change

            <

            SMALL_TRAJECTORY_CHANGE

        ):

            self.get_logger().warn(
                ""
            )

            self.get_logger().warn(
                "PROBLEM 3: TRAJECTORIES ARE ALMOST STATIC"
            )

            self.get_logger().warn(

                "Servo generates trajectories, but their "

                "total joint change is extremely small."

            )

            self.get_logger().warn(
                ""
            )

            self.get_logger().warn(
                "LIKELY CAUSE:"
            )

            self.get_logger().warn(

                "The Servo configuration or command scaling "

                "is producing movements too small to observe."

            )


        # CASO 4
        # ------------------------------------------------

        elif (

            self.max_desired_change_during_servo

            >

            REAL_MOVEMENT_THRESHOLD

            and

            self.max_actual_change_during_servo

            <=

            REAL_MOVEMENT_THRESHOLD

        ):

            self.get_logger().error(
                ""
            )

            self.get_logger().error(
                "PROBLEM 4: CONTROLLER DOES NOT EXECUTE COMMANDS"
            )

            self.get_logger().error(
                ""
            )

            self.get_logger().error(

                "Desired positions change, but actual "

                "positions remain almost constant."

            )

            self.get_logger().error(
                ""
            )

            self.get_logger().error(
                "THE PROBLEM IS LIKELY BETWEEN:"
            )

            self.get_logger().error(
                ""
            )

            self.get_logger().error(

                "joint_trajectory_controller"

            )

            self.get_logger().error(
                "        |"
            )

            self.get_logger().error(
                "        v"
            )

            self.get_logger().error(
                "ros2_control / gz_ros2_control"
            )


        # CASO 5
        # ------------------------------------------------

        elif (

            self.max_actual_change_during_servo

            >

            REAL_MOVEMENT_THRESHOLD

            and

            self.max_controller_error

            >

            CONTROLLER_ERROR_WARNING

        ):

            self.get_logger().warn(
                ""
            )

            self.get_logger().warn(
                "PROBLEM 5: ROBOT MOVES BUT CONTROLLER ERROR IS HIGH"
            )

            self.get_logger().warn(
                ""
            )

            self.get_logger().warn(

                "The controller executes the commands, "

                "but actual positions do not follow desired "

                "positions accurately."

            )


        # CASO 6
        # ------------------------------------------------

        elif (

            self.max_actual_change_during_servo

            >

            REAL_MOVEMENT_THRESHOLD

        ):

            self.get_logger().info(
                ""
            )

            self.get_logger().info(
                "SUCCESS: COMPLETE SERVO CHAIN IS WORKING"
            )

            self.get_logger().info(
                ""
            )

            self.get_logger().info(

                "Servo generates changing trajectories and "

                "the robot actually follows them."

            )


            if (

                self.max_total_trajectory_change

                <

                MEDIUM_TRAJECTORY_CHANGE

            ):

                self.get_logger().warn(
                    ""
                )

                self.get_logger().warn(

                    "However, the generated movement is "

                    "very small."

                )


        # CASO DESCONOCIDO
        # ------------------------------------------------

        else:

            self.get_logger().warn(
                ""
            )

            self.get_logger().warn(
                "INCONCLUSIVE RESULT"
            )

            self.get_logger().warn(

                "Servo and controller activity were detected, "

                "but the movement pattern does not match a "

                "clear failure category."

            )


        self.get_logger().info(
            ""
        )

        self.get_logger().info(
            "=================================================="
        )


# ============================================================
# MAIN
# ============================================================

def main(args=None):

    rclpy.init(
        args=args
    )


    node = ServoDiagnostic()


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

            "Diagnostic interrupted by user"

        )


    finally:

        node.print_final_report()

        node.destroy_node()

        rclpy.shutdown()


if __name__ == "__main__":

    main()