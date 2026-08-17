#!/usr/bin/env python3

"""
============================================================
 MOVEIT SERVO / UR5 / GAZEBO HARMONIC DIAGNOSTIC TOOL
============================================================

Este nodo NO controla el robot.

Su objetivo es monitorizar toda la cadena:

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

Mientras ejecutas tu ejercicio:

    HAL.MoveAbsJ(HOME, 0.8, 0.1)
    time.sleep(10.0)

    HAL.ServoForTime(
        0.02,
        0.0,
        0.0,
        10.0
    )

Este programa registra:

    - Joint states
    - Frecuencia de joint states
    - Cambios reales de las articulaciones
    - Comandos Twist enviados a Servo
    - Comandos JointJog enviados a Servo
    - Trayectorias enviadas al controller
    - Estado del controller
    - Posición deseada
    - Posición actual
    - Error del controller
    - TF disponibles
    - Nodos ROS activos
    - Topics ROS
    - Servicios importantes
    - Acciones importantes

Al finalizar muestra un resumen con posibles causas.
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

from tf2_ros import Buffer, TransformListener

import time
import threading
import subprocess
from collections import deque


# ============================================================
# CONFIGURACIÓN
# ============================================================

DIAGNOSTIC_DURATION = 30.0

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
# NODO
# ============================================================

class ServoDiagnostic(Node):

    def __init__(self):

        super().__init__("servo_diagnostic")

        # ----------------------------------------------------
        # QoS
        # ----------------------------------------------------

        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )

        reliable_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )

        # ----------------------------------------------------
        # VARIABLES DE DIAGNÓSTICO
        # ----------------------------------------------------

        self.start_time = time.time()

        # Joint states
        self.joint_state_count = 0
        self.first_joint_state = None
        self.last_joint_state = None

        self.initial_positions = None
        self.max_joint_change = 0.0

        self.joint_state_times = deque(maxlen=500)

        # Twist commands
        self.twist_count = 0
        self.last_twist = None
        self.first_twist_time = None

        # JointJog commands
        self.joint_jog_count = 0
        self.last_joint_jog = None
        self.first_joint_jog_time = None

        # Trajectories
        self.trajectory_count = 0
        self.last_trajectory = None
        self.first_trajectory_time = None

        # Controller state
        self.controller_state_count = 0

        self.last_actual_positions = None
        self.last_desired_positions = None
        self.last_error_positions = None

        # Flags
        self.expected_joints_found = False

        # ----------------------------------------------------
        # TF
        # ----------------------------------------------------

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(
            self.tf_buffer,
            self
        )

        # ----------------------------------------------------
        # SUBSCRIBERS
        # ----------------------------------------------------

        self.create_subscription(
            JointState,
            "/joint_states",
            self.joint_state_callback,
            qos
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
        # TIMER DE ESTADO
        # ----------------------------------------------------

        self.create_timer(
            1.0,
            self.print_live_status
        )

        self.get_logger().info(
            "=============================================="
        )

        self.get_logger().info(
            "MOVEIT SERVO DIAGNOSTIC STARTED"
        )

        self.get_logger().info(
            f"Diagnostic duration: {DIAGNOSTIC_DURATION} seconds"
        )

        self.get_logger().info(
            "Now execute your HAL program."
        )

        self.get_logger().info(
            "=============================================="
        )


    # ========================================================
    # JOINT STATES
    # ========================================================

    def joint_state_callback(self, msg):

        now = time.time()

        self.joint_state_count += 1
        self.joint_state_times.append(now)

        self.last_joint_state = msg

        if self.first_joint_state is None:

            self.first_joint_state = msg

            self.initial_positions = {
                name: position
                for name, position
                in zip(
                    msg.name,
                    msg.position
                )
            }

            self.get_logger().info(
                "[JOINT STATES] First message received"
            )

            missing = []

            for joint in EXPECTED_JOINTS:

                if joint not in msg.name:
                    missing.append(joint)

            if len(missing) == 0:

                self.expected_joints_found = True

                self.get_logger().info(
                    "[JOINT STATES] All expected UR joints found"
                )

            else:

                self.get_logger().warn(
                    f"[JOINT STATES] Missing joints: {missing}"
                )

        # -----------------------------------------------
        # DETECTAR MOVIMIENTO REAL
        # -----------------------------------------------

        if self.initial_positions is not None:

            for name, position in zip(
                msg.name,
                msg.position
            ):

                if name in self.initial_positions:

                    difference = abs(
                        position -
                        self.initial_positions[name]
                    )

                    if difference > self.max_joint_change:

                        self.max_joint_change = difference


    # ========================================================
    # TWIST COMMANDS
    # ========================================================

    def twist_callback(self, msg):

        self.twist_count += 1

        self.last_twist = msg

        if self.first_twist_time is None:

            self.first_twist_time = time.time()

            self.get_logger().info(
                "[SERVO INPUT] First Twist command received"
            )

        linear = msg.twist.linear
        angular = msg.twist.angular

        if self.twist_count <= 3:

            self.get_logger().info(
                "[SERVO INPUT] Twist received: "
                f"linear=["
                f"{linear.x:.6f}, "
                f"{linear.y:.6f}, "
                f"{linear.z:.6f}"
                f"] "
                f"angular=["
                f"{angular.x:.6f}, "
                f"{angular.y:.6f}, "
                f"{angular.z:.6f}"
                f"]"
            )


    # ========================================================
    # JOINT JOG
    # ========================================================

    def joint_jog_callback(self, msg):

        self.joint_jog_count += 1

        self.last_joint_jog = msg

        if self.first_joint_jog_time is None:

            self.first_joint_jog_time = time.time()

            self.get_logger().info(
                "[SERVO INPUT] First JointJog command received"
            )

        if self.joint_jog_count <= 3:

            self.get_logger().info(
                "[SERVO INPUT] JointJog received"
            )

            self.get_logger().info(
                f"  joints: {list(msg.joint_names)}"
            )

            self.get_logger().info(
                f"  velocities: {list(msg.velocities)}"
            )


    # ========================================================
    # TRAJECTORY
    # ========================================================

    def trajectory_callback(self, msg):

        self.trajectory_count += 1

        self.last_trajectory = msg

        if self.first_trajectory_time is None:

            self.first_trajectory_time = time.time()

            self.get_logger().info(
                "[SERVO OUTPUT] First JointTrajectory received"
            )

        if self.trajectory_count <= 3:

            self.get_logger().info(
                "[SERVO OUTPUT] Trajectory received"
            )

            self.get_logger().info(
                f"  joints: {list(msg.joint_names)}"
            )

            self.get_logger().info(
                f"  number of points: {len(msg.points)}"
            )

            if len(msg.points) > 0:

                self.get_logger().info(
                    f"  positions: "
                    f"{list(msg.points[0].positions)}"
                )

                self.get_logger().info(
                    f"  velocities: "
                    f"{list(msg.points[0].velocities)}"
                )


    # ========================================================
    # CONTROLLER STATE
    # ========================================================

    def controller_state_callback(self, msg):

        self.controller_state_count += 1

        try:

            self.last_actual_positions = list(
                msg.actual.positions
            )

            self.last_desired_positions = list(
                msg.desired.positions
            )

            self.last_error_positions = list(
                msg.error.positions
            )

        except Exception as e:

            self.get_logger().warn(
                f"Error reading controller state: {e}"
            )


    # ========================================================
    # FRECUENCIA JOINT STATES
    # ========================================================

    def get_joint_state_frequency(self):

        if len(self.joint_state_times) < 2:
            return 0.0

        first = self.joint_state_times[0]
        last = self.joint_state_times[-1]

        elapsed = last - first

        if elapsed <= 0:
            return 0.0

        return (
            len(self.joint_state_times) - 1
        ) / elapsed


    # ========================================================
    # ESTADO EN VIVO
    # ========================================================

    def print_live_status(self):

        elapsed = time.time() - self.start_time

        joint_frequency = (
            self.get_joint_state_frequency()
        )

        self.get_logger().info(
            "------------------------------------------"
        )

        self.get_logger().info(
            f"TIME: {elapsed:.1f} / "
            f"{DIAGNOSTIC_DURATION:.1f} s"
        )

        self.get_logger().info(
            f"joint_states: "
            f"{self.joint_state_count} messages "
            f"({joint_frequency:.1f} Hz)"
        )

        self.get_logger().info(
            f"twist commands: "
            f"{self.twist_count}"
        )

        self.get_logger().info(
            f"joint jog commands: "
            f"{self.joint_jog_count}"
        )

        self.get_logger().info(
            f"trajectories: "
            f"{self.trajectory_count}"
        )

        self.get_logger().info(
            f"controller states: "
            f"{self.controller_state_count}"
        )

        self.get_logger().info(
            f"maximum joint movement: "
            f"{self.max_joint_change:.6f} rad"
        )


    # ========================================================
    # COMPROBAR TF
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
    # EJECUTAR COMANDO ROS
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
    # COMPROBAR SISTEMA ROS
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
            "nodes": nodes_output.splitlines(),
            "topics": topics_output.splitlines(),
            "services": services_output.splitlines(),
            "actions": actions_output.splitlines(),
        }


    # ========================================================
    # RESUMEN FINAL
    # ========================================================

    def print_final_report(self):

        self.get_logger().info("")
        self.get_logger().info(
            "=================================================="
        )

        self.get_logger().info(
            "FINAL DIAGNOSTIC REPORT"
        )

        self.get_logger().info(
            "=================================================="
        )

        # --------------------------------------------------
        # JOINT STATES
        # --------------------------------------------------

        frequency = (
            self.get_joint_state_frequency()
        )

        if self.joint_state_count > 0:

            self.get_logger().info(
                "[OK] /joint_states is publishing"
            )

            self.get_logger().info(
                f"     Messages: {self.joint_state_count}"
            )

            self.get_logger().info(
                f"     Frequency: {frequency:.2f} Hz"
            )

        else:

            self.get_logger().error(
                "[FAIL] No /joint_states received"
            )

        # --------------------------------------------------
        # EXPECTED JOINTS
        # --------------------------------------------------

        if self.expected_joints_found:

            self.get_logger().info(
                "[OK] All expected UR joints found"
            )

        else:

            self.get_logger().error(
                "[FAIL] Expected UR joints missing"
            )

        # --------------------------------------------------
        # SERVO INPUT
        # --------------------------------------------------

        if self.twist_count > 0:

            self.get_logger().info(
                "[OK] Twist commands reached Servo input"
            )

            self.get_logger().info(
                f"     Total Twist messages: "
                f"{self.twist_count}"
            )

        else:

            self.get_logger().error(
                "[FAIL] No Twist commands received"
            )

            self.get_logger().error(
                "       HAL.ServoForTime may not be publishing "
                "to /servo_node/delta_twist_cmds"
            )

        # --------------------------------------------------
        # JOINT JOG
        # --------------------------------------------------

        if self.joint_jog_count > 0:

            self.get_logger().info(
                "[OK] JointJog commands received"
            )

        else:

            self.get_logger().warn(
                "[WARN] No JointJog commands received"
            )

            self.get_logger().warn(
                "       This may be normal if Cartesian "
                "Twist commands are being used"
            )

        # --------------------------------------------------
        # SERVO OUTPUT
        # --------------------------------------------------

        if self.trajectory_count > 0:

            self.get_logger().info(
                "[OK] Servo generated trajectories"
            )

            self.get_logger().info(
                f"     Total trajectories: "
                f"{self.trajectory_count}"
            )

        else:

            self.get_logger().error(
                "[FAIL] No trajectories detected"
            )

            if self.twist_count > 0:

                self.get_logger().error(
                    "       Commands reach Servo but Servo does "
                    "not generate output"
                )

        # --------------------------------------------------
        # CONTROLLER
        # --------------------------------------------------

        if self.controller_state_count > 0:

            self.get_logger().info(
                "[OK] Controller state received"
            )

            if self.last_actual_positions is not None:

                self.get_logger().info(
                    "     Actual positions:"
                )

                self.get_logger().info(
                    f"     {self.last_actual_positions}"
                )

            if self.last_desired_positions is not None:

                self.get_logger().info(
                    "     Desired positions:"
                )

                self.get_logger().info(
                    f"     {self.last_desired_positions}"
                )

            if self.last_error_positions is not None:

                self.get_logger().info(
                    "     Error positions:"
                )

                self.get_logger().info(
                    f"     {self.last_error_positions}"
                )

        else:

            self.get_logger().error(
                "[FAIL] No controller state received"
            )

        # --------------------------------------------------
        # MOVIMIENTO REAL
        # --------------------------------------------------

        self.get_logger().info(
            "--------------------------------------------------"
        )

        if self.max_joint_change > 0.001:

            self.get_logger().info(
                "[OK] REAL ROBOT MOVEMENT DETECTED"
            )

            self.get_logger().info(
                f"     Maximum joint change: "
                f"{self.max_joint_change:.6f} rad"
            )

        else:

            self.get_logger().error(
                "[FAIL] ROBOT DID NOT MOVE"
            )

            self.get_logger().error(
                f"       Maximum joint change: "
                f"{self.max_joint_change:.8f} rad"
            )

        # --------------------------------------------------
        # TF
        # --------------------------------------------------

        self.get_logger().info(
            "--------------------------------------------------"
        )

        self.get_logger().info(
            "TF CHECK"
        )

        tf_results = self.check_tf()

        for source, target, success, data in tf_results:

            if success:

                self.get_logger().info(
                    f"[OK] TF available: "
                    f"{source} -> {target}"
                )

            else:

                self.get_logger().error(
                    f"[FAIL] TF missing: "
                    f"{source} -> {target}"
                )

                self.get_logger().error(
                    f"       {data}"
                )

        # --------------------------------------------------
        # ROS GRAPH
        # --------------------------------------------------

        self.get_logger().info(
            "--------------------------------------------------"
        )

        self.get_logger().info(
            "ROS GRAPH CHECK"
        )

        graph = self.check_ros_graph()

        # Nodes

        for node in IMPORTANT_NODES:

            if node in graph["nodes"]:

                self.get_logger().info(
                    f"[OK] Node exists: {node}"
                )

            else:

                self.get_logger().warn(
                    f"[WARN] Node not found: {node}"
                )

        # Topics

        for topic in IMPORTANT_TOPICS:

            if topic in graph["topics"]:

                self.get_logger().info(
                    f"[OK] Topic exists: {topic}"
                )

            else:

                self.get_logger().warn(
                    f"[WARN] Topic not found: {topic}"
                )

        # Services

        for service in IMPORTANT_SERVICES:

            if service in graph["services"]:

                self.get_logger().info(
                    f"[OK] Service exists: {service}"
                )

            else:

                self.get_logger().warn(
                    f"[WARN] Service not found: {service}"
                )

        # Actions

        for action in IMPORTANT_ACTIONS:

            if action in graph["actions"]:

                self.get_logger().info(
                    f"[OK] Action exists: {action}"
                )

            else:

                self.get_logger().warn(
                    f"[WARN] Action not found: {action}"
                )

        # --------------------------------------------------
        # CONCLUSIÓN AUTOMÁTICA
        # --------------------------------------------------

        self.get_logger().info("")
        self.get_logger().info(
            "=================================================="
        )

        self.get_logger().info(
            "AUTOMATIC CONCLUSION"
        )

        self.get_logger().info(
            "=================================================="
        )

        if self.twist_count == 0:

            self.get_logger().error(
                "PROBLEM 1:"
            )

            self.get_logger().error(
                "HAL.ServoForTime() is not publishing "
                "Twist commands to the expected Servo topic."
            )

        elif self.trajectory_count == 0:

            self.get_logger().error(
                "PROBLEM 2:"
            )

            self.get_logger().error(
                "Servo receives commands but does not "
                "generate trajectories."
            )

            self.get_logger().error(
                "Possible causes:"
            )

            self.get_logger().error(
                "- Servo is paused"
            )

            self.get_logger().error(
                "- Wrong planning group"
            )

            self.get_logger().error(
                "- Wrong command frame"
            )

            self.get_logger().error(
                "- Missing or invalid TF"
            )

            self.get_logger().error(
                "- Collision / singularity / workspace limitation"
            )

        elif self.max_joint_change <= 0.001:

            self.get_logger().error(
                "PROBLEM 3:"
            )

            self.get_logger().error(
                "Servo generates trajectories but "
                "the robot does not move."
            )

            self.get_logger().error(
                "The problem is probably between:"
            )

            self.get_logger().error(
                "joint_trajectory_controller"
            )

            self.get_logger().error(
                "and ros2_control / Gazebo."
            )

        else:

            self.get_logger().info(
                "SUCCESS:"
            )

            self.get_logger().info(
                "The complete Servo chain appears to be working."
            )

        self.get_logger().info(
            "=================================================="
        )


# ============================================================
# MAIN
# ============================================================

def main(args=None):

    rclpy.init(args=args)

    node = ServoDiagnostic()

    start = time.time()

    try:

        while rclpy.ok():

            rclpy.spin_once(
                node,
                timeout_sec=0.1
            )

            elapsed = time.time() - start

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