#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import TwistStamped
from trajectory_msgs.msg import JointTrajectory
from sensor_msgs.msg import JointState
from control_msgs.msg import JointTrajectoryControllerState

import math
import time


class ServoChainDiagnostic(Node):

    def __init__(self):

        super().__init__('servo_chain_diagnostic')

        # ============================================================
        # CONFIGURATION
        # ============================================================

        self.duration = 60.0
        self.start_time = time.time()

        self.joint_names_expected = [
            'shoulder_pan_joint',
            'shoulder_lift_joint',
            'elbow_joint',
            'wrist_1_joint',
            'wrist_2_joint',
            'wrist_3_joint'
        ]

        # ============================================================
        # DATA
        # ============================================================

        self.twist_count = 0
        self.trajectory_count = 0
        self.joint_state_count = 0
        self.controller_state_count = 0

        self.first_twist_time = None
        self.last_twist_time = None

        self.last_twist = None

        self.last_trajectory = None
        self.first_trajectory = None

        self.last_real_positions = {}
        self.first_real_positions = None

        self.last_desired_positions = {}
        self.last_controller_actual_positions = {}

        self.max_trajectory_step = 0.0
        self.max_trajectory_total_change = 0.0

        self.max_real_change = 0.0

        self.max_controller_error = 0.0
        self.sum_controller_error = 0.0
        self.controller_error_samples = 0

        self.max_joint_velocity = {
            joint: 0.0
            for joint in self.joint_names_expected
        }

        self.previous_joint_positions = None
        self.previous_joint_time = None

        # Historial de movimiento durante Servo
        self.servo_started = False
        self.servo_start_real_positions = None

        # Estadísticas de trayectorias
        self.identical_trajectory_count = 0

        self.min_time_from_start = None
        self.max_time_from_start = None
        self.sum_time_from_start = 0.0
        self.time_from_start_samples = 0

        self.zero_duration_trajectories = 0

        # ============================================================
        # SUBSCRIBERS
        # ============================================================

        self.create_subscription(
            TwistStamped,
            '/servo_node/delta_twist_cmds',
            self.twist_callback,
            100
        )

        self.create_subscription(
            JointTrajectory,
            '/joint_trajectory_controller/joint_trajectory',
            self.trajectory_callback,
            1000
        )

        self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            100
        )

        self.create_subscription(
            JointTrajectoryControllerState,
            '/joint_trajectory_controller/state',
            self.controller_state_callback,
            100
        )

        # ============================================================
        # TIMER
        # ============================================================

        self.create_timer(2.0, self.print_status)

        self.create_timer(
            self.duration,
            self.finish_diagnostic
        )

        self.get_logger().info('')
        self.get_logger().info('=' * 70)
        self.get_logger().info('MOVEIT SERVO CHAIN DIAGNOSTIC')
        self.get_logger().info('=' * 70)
        self.get_logger().info(
            f'Duration: {self.duration:.1f} seconds'
        )
        self.get_logger().info('')
        self.get_logger().info(
            'Run your HAL program now.'
        )
        self.get_logger().info(
            'This node will analyse the complete chain:'
        )
        self.get_logger().info('')
        self.get_logger().info(
            'HAL -> Twist -> Servo -> Trajectory -> Controller -> Robot'
        )
        self.get_logger().info('=' * 70)

    # ================================================================
    # TWIST CALLBACK
    # ================================================================

    def twist_callback(self, msg):

        now = time.time()

        self.twist_count += 1

        if self.first_twist_time is None:

            self.first_twist_time = now

            if not self.servo_started:

                self.servo_started = True

                self.get_logger().info('')
                self.get_logger().info('=' * 60)
                self.get_logger().info('[SERVO START DETECTED]')
                self.get_logger().info('=' * 60)

                if self.last_real_positions:

                    self.servo_start_real_positions = \
                        self.last_real_positions.copy()

                    self.get_logger().info(
                        'Robot position before Servo:'
                    )

                    self.print_joint_dict(
                        self.servo_start_real_positions
                    )

        self.last_twist_time = now
        self.last_twist = msg

    # ================================================================
    # TRAJECTORY CALLBACK
    # ================================================================

    def trajectory_callback(self, msg):

        self.trajectory_count += 1

        if len(msg.points) == 0:
            return

        point = msg.points[-1]

        if len(point.positions) == 0:
            return

        trajectory = {}

        for i, joint in enumerate(msg.joint_names):

            if i < len(point.positions):

                trajectory[joint] = point.positions[i]

        # ------------------------------------------------------------
        # TIME FROM START
        # ------------------------------------------------------------

        duration = (
            point.time_from_start.sec +
            point.time_from_start.nanosec * 1e-9
        )

        self.sum_time_from_start += duration
        self.time_from_start_samples += 1

        if self.min_time_from_start is None:

            self.min_time_from_start = duration
            self.max_time_from_start = duration

        else:

            self.min_time_from_start = min(
                self.min_time_from_start,
                duration
            )

            self.max_time_from_start = max(
                self.max_time_from_start,
                duration
            )

        if duration <= 0.0:

            self.zero_duration_trajectories += 1

        # ------------------------------------------------------------
        # FIRST TRAJECTORY
        # ------------------------------------------------------------

        if self.first_trajectory is None:

            self.first_trajectory = trajectory.copy()

            self.get_logger().info('')
            self.get_logger().info(
                '[SERVO OUTPUT] First trajectory detected'
            )

            self.get_logger().info(
                f'Time from start: {duration:.9f} s'
            )

        # ------------------------------------------------------------
        # COMPARE WITH PREVIOUS TRAJECTORY
        # ------------------------------------------------------------

        if self.last_trajectory is not None:

            max_step = 0.0

            for joint in trajectory:

                if joint in self.last_trajectory:

                    difference = abs(
                        trajectory[joint]
                        - self.last_trajectory[joint]
                    )

                    max_step = max(
                        max_step,
                        difference
                    )

            self.max_trajectory_step = max(
                self.max_trajectory_step,
                max_step
            )

            if max_step < 1e-8:

                self.identical_trajectory_count += 1

        # ------------------------------------------------------------
        # TOTAL CHANGE FROM FIRST TRAJECTORY
        # ------------------------------------------------------------

        if self.first_trajectory is not None:

            max_total_change = 0.0

            for joint in trajectory:

                if joint in self.first_trajectory:

                    difference = abs(
                        trajectory[joint]
                        - self.first_trajectory[joint]
                    )

                    max_total_change = max(
                        max_total_change,
                        difference
                    )

            self.max_trajectory_total_change = max(
                self.max_trajectory_total_change,
                max_total_change
            )

        self.last_trajectory = trajectory

    # ================================================================
    # JOINT STATES CALLBACK
    # ================================================================

    def joint_state_callback(self, msg):

        self.joint_state_count += 1

        current_positions = {}

        for i, joint in enumerate(msg.name):

            if i < len(msg.position):

                current_positions[joint] = msg.position[i]

        # ------------------------------------------------------------
        # CALCULATE REAL JOINT VELOCITIES
        # ------------------------------------------------------------

        now = time.time()

        if (
            self.previous_joint_positions is not None
            and self.previous_joint_time is not None
        ):

            dt = now - self.previous_joint_time

            if dt > 0.0:

                for joint in current_positions:

                    if joint in self.previous_joint_positions:

                        velocity = abs(
                            current_positions[joint]
                            - self.previous_joint_positions[joint]
                        ) / dt

                        if joint in self.max_joint_velocity:

                            self.max_joint_velocity[joint] = max(
                                self.max_joint_velocity[joint],
                                velocity
                            )

        self.previous_joint_positions = \
            current_positions.copy()

        self.previous_joint_time = now

        # ------------------------------------------------------------
        # SAVE REAL POSITIONS
        # ------------------------------------------------------------

        relevant_positions = {}

        for joint in self.joint_names_expected:

            if joint in current_positions:

                relevant_positions[joint] = \
                    current_positions[joint]

        self.last_real_positions = relevant_positions

        # ------------------------------------------------------------
        # REAL MOVEMENT DURING SERVO
        # ------------------------------------------------------------

        if (
            self.servo_started
            and self.servo_start_real_positions is not None
        ):

            for joint in relevant_positions:

                if joint in self.servo_start_real_positions:

                    difference = abs(
                        relevant_positions[joint]
                        - self.servo_start_real_positions[joint]
                    )

                    self.max_real_change = max(
                        self.max_real_change,
                        difference
                    )

    # ================================================================
    # CONTROLLER STATE CALLBACK
    # ================================================================

    def controller_state_callback(self, msg):

        self.controller_state_count += 1

        joint_names = msg.joint_names

        # desired / actual son JointTrajectoryPoint

        for i, joint in enumerate(joint_names):

            if (
                i < len(msg.desired.positions)
                and i < len(msg.actual.positions)
            ):

                desired = msg.desired.positions[i]
                actual = msg.actual.positions[i]

                error = abs(
                    desired - actual
                )

                self.last_desired_positions[joint] = desired
                self.last_controller_actual_positions[joint] = actual

                self.max_controller_error = max(
                    self.max_controller_error,
                    error
                )

                self.sum_controller_error += error
                self.controller_error_samples += 1

    # ================================================================
    # PRINT STATUS
    # ================================================================

    def print_status(self):

        elapsed = time.time() - self.start_time

        if elapsed > self.duration:
            return

        self.get_logger().info('')
        self.get_logger().info('-' * 55)
        self.get_logger().info(
            f'TIME: {elapsed:.1f} / {self.duration:.1f} s'
        )

        self.get_logger().info(
            f'Joint states: {self.joint_state_count}'
        )

        self.get_logger().info(
            f'Twist messages: {self.twist_count}'
        )

        self.get_logger().info(
            f'Trajectories: {self.trajectory_count}'
        )

        self.get_logger().info(
            f'Controller states: {self.controller_state_count}'
        )

        self.get_logger().info(
            'Max trajectory step: '
            f'{self.max_trajectory_step:.10f} rad'
        )

        self.get_logger().info(
            'Max trajectory total change: '
            f'{self.max_trajectory_total_change:.10f} rad'
        )

        self.get_logger().info(
            'Max real robot change: '
            f'{self.max_real_change:.10f} rad'
        )

        self.get_logger().info(
            'Max controller error: '
            f'{self.max_controller_error:.10f} rad'
        )

        if self.last_trajectory is not None:

            self.get_logger().info(
                'Latest Servo trajectory:'
            )

            self.print_joint_dict(
                self.last_trajectory
            )

        if self.last_real_positions:

            self.get_logger().info(
                'Latest real robot position:'
            )

            self.print_joint_dict(
                self.last_real_positions
            )

    # ================================================================
    # FINAL REPORT
    # ================================================================

    def finish_diagnostic(self):

        elapsed = time.time() - self.start_time

        self.get_logger().info('')
        self.get_logger().info('=' * 70)
        self.get_logger().info(
            'FINAL MOVEIT SERVO CHAIN DIAGNOSTIC'
        )
        self.get_logger().info('=' * 70)

        # ------------------------------------------------------------
        # 1. TWIST
        # ------------------------------------------------------------

        self.get_logger().info('')
        self.get_logger().info(
            '1. TWIST INPUT'
        )
        self.get_logger().info('-' * 50)

        self.get_logger().info(
            f'Total Twist messages: {self.twist_count}'
        )

        if (
            self.first_twist_time is not None
            and self.last_twist_time is not None
            and self.last_twist_time > self.first_twist_time
        ):

            twist_duration = (
                self.last_twist_time
                - self.first_twist_time
            )

            frequency = (
                self.twist_count
                / twist_duration
            )

            self.get_logger().info(
                f'Twist frequency: {frequency:.4f} Hz'
            )

        if self.last_twist is not None:

            linear = self.last_twist.twist.linear
            angular = self.last_twist.twist.angular

            self.get_logger().info(
                'Last Twist linear: '
                f'[{linear.x:.8f}, '
                f'{linear.y:.8f}, '
                f'{linear.z:.8f}]'
            )

            self.get_logger().info(
                'Last Twist angular: '
                f'[{angular.x:.8f}, '
                f'{angular.y:.8f}, '
                f'{angular.z:.8f}]'
            )

        # ------------------------------------------------------------
        # 2. TRAJECTORIES
        # ------------------------------------------------------------

        self.get_logger().info('')
        self.get_logger().info(
            '2. SERVO TRAJECTORY OUTPUT'
        )
        self.get_logger().info('-' * 50)

        self.get_logger().info(
            f'Total trajectories: {self.trajectory_count}'
        )

        self.get_logger().info(
            'Maximum step between trajectories: '
            f'{self.max_trajectory_step:.10f} rad'
        )

        self.get_logger().info(
            'Maximum accumulated trajectory change: '
            f'{self.max_trajectory_total_change:.10f} rad'
        )

        if self.trajectory_count > 0:

            identical_percentage = (
                100.0
                * self.identical_trajectory_count
                / self.trajectory_count
            )

            self.get_logger().info(
                f'Almost identical trajectories: '
                f'{self.identical_trajectory_count}'
            )

            self.get_logger().info(
                f'Identical percentage: '
                f'{identical_percentage:.4f}%'
            )

        # ------------------------------------------------------------
        # 3. TIME FROM START
        # ------------------------------------------------------------

        self.get_logger().info('')
        self.get_logger().info(
            '3. TRAJECTORY TIMING'
        )
        self.get_logger().info('-' * 50)

        if self.time_from_start_samples > 0:

            average_time = (
                self.sum_time_from_start
                / self.time_from_start_samples
            )

            self.get_logger().info(
                'Minimum time_from_start: '
                f'{self.min_time_from_start:.12f} s'
            )

            self.get_logger().info(
                'Maximum time_from_start: '
                f'{self.max_time_from_start:.12f} s'
            )

            self.get_logger().info(
                'Average time_from_start: '
                f'{average_time:.12f} s'
            )

            self.get_logger().info(
                f'Zero duration trajectories: '
                f'{self.zero_duration_trajectories}'
            )

        # ------------------------------------------------------------
        # 4. REAL MOVEMENT
        # ------------------------------------------------------------

        self.get_logger().info('')
        self.get_logger().info(
            '4. REAL ROBOT MOVEMENT'
        )
        self.get_logger().info('-' * 50)

        self.get_logger().info(
            'Maximum real movement: '
            f'{self.max_real_change:.10f} rad'
        )

        self.get_logger().info(
            'Maximum real movement: '
            f'{math.degrees(self.max_real_change):.10f} deg'
        )

        # ------------------------------------------------------------
        # 5. JOINT VELOCITIES
        # ------------------------------------------------------------

        self.get_logger().info('')
        self.get_logger().info(
            '5. MAXIMUM REAL JOINT VELOCITIES'
        )
        self.get_logger().info('-' * 50)

        for joint in self.joint_names_expected:

            velocity = self.max_joint_velocity.get(
                joint,
                0.0
            )

            self.get_logger().info(
                f'{joint}: {velocity:.10f} rad/s'
            )

        # ------------------------------------------------------------
        # 6. CONTROLLER ERROR
        # ------------------------------------------------------------

        self.get_logger().info('')
        self.get_logger().info(
            '6. CONTROLLER FOLLOWING ERROR'
        )
        self.get_logger().info('-' * 50)

        self.get_logger().info(
            'Maximum controller error: '
            f'{self.max_controller_error:.10f} rad'
        )

        if self.controller_error_samples > 0:

            average_error = (
                self.sum_controller_error
                / self.controller_error_samples
            )

            self.get_logger().info(
                'Average controller error: '
                f'{average_error:.10f} rad'
            )

        # ------------------------------------------------------------
        # 7. FINAL CHAIN
        # ------------------------------------------------------------

        self.get_logger().info('')
        self.get_logger().info(
            '7. COMPLETE CHAIN'
        )
        self.get_logger().info('-' * 50)

        if self.last_twist is not None:

            self.get_logger().info(
                'Input Twist:'
            )

            self.get_logger().info(
                f'linear.x = '
                f'{self.last_twist.twist.linear.x:.10f}'
            )

            self.get_logger().info(
                f'linear.y = '
                f'{self.last_twist.twist.linear.y:.10f}'
            )

            self.get_logger().info(
                f'linear.z = '
                f'{self.last_twist.twist.linear.z:.10f}'
            )

        self.get_logger().info(
            'Servo generated movement: '
            f'{self.max_trajectory_total_change:.10f} rad'
        )

        self.get_logger().info(
            'Real robot movement: '
            f'{self.max_real_change:.10f} rad'
        )

        # ------------------------------------------------------------
        # DIAGNOSIS
        # ------------------------------------------------------------

        self.get_logger().info('')
        self.get_logger().info('=' * 70)
        self.get_logger().info(
            'AUTOMATIC DIAGNOSIS'
        )
        self.get_logger().info('=' * 70)

        if self.twist_count == 0:

            self.get_logger().error(
                '[FAIL] No Twist commands detected.'
            )

        elif self.trajectory_count == 0:

            self.get_logger().error(
                '[FAIL] Servo receives Twist but generates no trajectories.'
            )

        elif self.max_trajectory_total_change < 1e-4:

            self.get_logger().warn(
                '[WARNING] Servo generates trajectories, '
                'but the generated joint movement is extremely small.'
            )

            self.get_logger().warn(
                'Likely causes:'
            )

            self.get_logger().warn(
                '  - Servo scaling too low'
            )

            self.get_logger().warn(
                '  - Singularity scaling'
            )

            self.get_logger().warn(
                '  - Collision scaling'
            )

            self.get_logger().warn(
                '  - Incorrect Jacobian / robot configuration'
            )

        if (
            self.max_trajectory_total_change > 1e-5
            and self.max_real_change
            < self.max_trajectory_total_change * 0.1
        ):

            self.get_logger().warn(
                '[WARNING] Servo generates movement '
                'but the robot does not follow it.'
            )

            self.get_logger().warn(
                'Likely problem is after MoveIt Servo:'
            )

            self.get_logger().warn(
                '  Servo -> joint_trajectory_controller -> robot'
            )

        if self.max_controller_error > 0.05:

            self.get_logger().warn(
                '[WARNING] Large controller tracking error detected.'
            )

            self.get_logger().warn(
                'The controller may not be capable of following '
                'the high-frequency Servo trajectories.'
            )

        if self.time_from_start_samples > 0:

            average_time = (
                self.sum_time_from_start
                / self.time_from_start_samples
            )

            if average_time < 0.005:

                self.get_logger().warn(
                    '[WARNING] Extremely small trajectory time_from_start.'
                )

                self.get_logger().warn(
                    'The controller may be receiving trajectory points '
                    'with an execution time that is too short.'
                )

        self.get_logger().info('')
        self.get_logger().info(
            'Diagnostic finished.'
        )

        self.get_logger().info('=' * 70)

        rclpy.shutdown()

    # ================================================================
    # HELPER
    # ================================================================

    def print_joint_dict(self, values):

        for joint in self.joint_names_expected:

            if joint in values:

                value = values[joint]

                self.get_logger().info(
                    f'  {joint}: '
                    f'{value:.10f} rad '
                    f'({math.degrees(value):.6f} deg)'
                )


def main(args=None):

    rclpy.init(args=args)

    node = ServoChainDiagnostic()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    finally:

        if rclpy.ok():

            rclpy.shutdown()


if __name__ == '__main__':

    main()