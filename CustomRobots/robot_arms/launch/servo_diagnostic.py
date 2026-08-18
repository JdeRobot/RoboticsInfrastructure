#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory
from control_msgs.msg import JointTrajectoryControllerState

import math
import time


JOINTS = [
    'shoulder_pan_joint',
    'shoulder_lift_joint',
    'elbow_joint',
    'wrist_1_joint',
    'wrist_2_joint',
    'wrist_3_joint'
]


class ServoControllerDebug(Node):

    def __init__(self):
        super().__init__('servo_controller_debug')

        self.start_time = time.time()

        self.real_positions = {}
        self.initial_real_position = None

        self.last_trajectory = None
        self.last_trajectory_time = None

        self.trajectory_count = 0
        self.controller_count = 0
        self.joint_state_count = 0

        self.first_trajectory_detected = False

        self.max_real_movement = 0.0
        self.max_command_difference = 0.0
        self.max_controller_error = 0.0

        self.previous_trajectory_positions = None

        self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            100
        )

        self.create_subscription(
            JointTrajectory,
            '/joint_trajectory_controller/joint_trajectory',
            self.trajectory_callback,
            100
        )

        self.create_subscription(
            JointTrajectoryControllerState,
            '/joint_trajectory_controller/state',
            self.controller_callback,
            100
        )

        self.create_timer(1.0, self.print_status)

        self.get_logger().info('')
        self.get_logger().info('=' * 70)
        self.get_logger().info('MOVEIT SERVO -> CONTROLLER DEEP DEBUG')
        self.get_logger().info('=' * 70)
        self.get_logger().info('')
        self.get_logger().info(
            'Execute your HAL program now.'
        )
        self.get_logger().info('')
        self.get_logger().info(
            'This diagnostic compares every stage:'
        )
        self.get_logger().info('')
        self.get_logger().info(
            'Servo trajectory -> Controller desired -> '
            'Controller actual -> Joint states'
        )
        self.get_logger().info('')
        self.get_logger().info('=' * 70)

    # ---------------------------------------------------------
    # JOINT STATES
    # ---------------------------------------------------------

    def joint_state_callback(self, msg):

        self.joint_state_count += 1

        for name, position in zip(msg.name, msg.position):

            if name in JOINTS:
                self.real_positions[name] = position

        if self.first_trajectory_detected:

            if self.initial_real_position is not None:

                for joint in JOINTS:

                    if (
                        joint in self.real_positions
                        and joint in self.initial_real_position
                    ):

                        movement = abs(
                            self.real_positions[joint]
                            -
                            self.initial_real_position[joint]
                        )

                        if movement > self.max_real_movement:

                            self.max_real_movement = movement

    # ---------------------------------------------------------
    # TRAJECTORY FROM SERVO
    # ---------------------------------------------------------

    def trajectory_callback(self, msg):

        self.trajectory_count += 1

        if len(msg.points) == 0:
            self.get_logger().warning(
                '[TRAJECTORY] Received trajectory with ZERO points'
            )
            return

        point = msg.points[-1]

        trajectory_positions = {}

        for name, position in zip(
            msg.joint_names,
            point.positions
        ):

            if name in JOINTS:
                trajectory_positions[name] = position

        # Detect first trajectory

        if not self.first_trajectory_detected:

            self.first_trajectory_detected = True

            self.initial_real_position = dict(
                self.real_positions
            )

            self.get_logger().info('')
            self.get_logger().info('=' * 70)
            self.get_logger().info(
                '[SERVO START] FIRST TRAJECTORY RECEIVED'
            )
            self.get_logger().info('=' * 70)

            self.get_logger().info('')

            self.get_logger().info(
                'Robot position BEFORE Servo:'
            )

            for joint in JOINTS:

                value = self.initial_real_position.get(
                    joint,
                    float('nan')
                )

                self.get_logger().info(
                    f'  {joint}: {value:.10f} rad'
                )

            self.get_logger().info('')
            self.get_logger().info(
                'FIRST SERVO TRAJECTORY:'
            )

            for joint in JOINTS:

                value = trajectory_positions.get(
                    joint,
                    float('nan')
                )

                self.get_logger().info(
                    f'  {joint}: {value:.10f} rad'
                )

            self.get_logger().info('')

            self.get_logger().info(
                f'Trajectory points: {len(msg.points)}'
            )

            self.get_logger().info(
                'time_from_start: '
                f'{point.time_from_start.sec}.'
                f'{point.time_from_start.nanosec:09d} s'
            )

            self.get_logger().info(
                f'Positions count: {len(point.positions)}'
            )

            self.get_logger().info(
                f'Velocities count: {len(point.velocities)}'
            )

            self.get_logger().info('=' * 70)

        # Compare with previous trajectory

        if self.previous_trajectory_positions is not None:

            for joint in JOINTS:

                if (
                    joint in trajectory_positions
                    and joint in self.previous_trajectory_positions
                ):

                    difference = abs(
                        trajectory_positions[joint]
                        -
                        self.previous_trajectory_positions[joint]
                    )

                    if difference > self.max_command_difference:

                        self.max_command_difference = difference

        self.previous_trajectory_positions = dict(
            trajectory_positions
        )

        self.last_trajectory = trajectory_positions
        self.last_trajectory_time = time.time()

    # ---------------------------------------------------------
    # CONTROLLER STATE
    # ---------------------------------------------------------

    def controller_callback(self, msg):

        self.controller_count += 1

        joint_names = msg.joint_names

        desired = {}
        actual = {}
        error = {}

        for i, joint in enumerate(joint_names):

            if joint not in JOINTS:
                continue

            if i < len(msg.desired.positions):

                desired[joint] = (
                    msg.desired.positions[i]
                )

            if i < len(msg.actual.positions):

                actual[joint] = (
                    msg.actual.positions[i]
                )

            if i < len(msg.error.positions):

                error[joint] = (
                    msg.error.positions[i]
                )

                value = abs(error[joint])

                if value > self.max_controller_error:

                    self.max_controller_error = value

        # Print interesting controller errors

        for joint in JOINTS:

            if joint not in error:
                continue

            if abs(error[joint]) > 0.01:

                self.get_logger().warning(
                    '[CONTROLLER ERROR] '
                    f'{joint}: '
                    f'error={error[joint]:.8f} rad '
                    f'desired={desired.get(joint, 0.0):.8f} '
                    f'actual={actual.get(joint, 0.0):.8f}'
                )

    # ---------------------------------------------------------
    # PERIODIC STATUS
    # ---------------------------------------------------------

    def print_status(self):

        elapsed = time.time() - self.start_time

        self.get_logger().info('')
        self.get_logger().info('-' * 70)

        self.get_logger().info(
            f'TIME: {elapsed:.1f} s'
        )

        self.get_logger().info('')

        self.get_logger().info(
            f'Joint states: {self.joint_state_count}'
        )

        self.get_logger().info(
            f'Servo trajectories: {self.trajectory_count}'
        )

        self.get_logger().info(
            f'Controller states: {self.controller_count}'
        )

        self.get_logger().info('')

        self.get_logger().info(
            'MAXIMUM VALUES'
        )

        self.get_logger().info(
            f'Max difference between Servo trajectories: '
            f'{self.max_command_difference:.10f} rad'
        )

        self.get_logger().info(
            f'Max real robot movement: '
            f'{self.max_real_movement:.10f} rad'
        )

        self.get_logger().info(
            f'Max controller error: '
            f'{self.max_controller_error:.10f} rad'
        )

        # Last trajectory comparison

        if self.last_trajectory is not None:

            self.get_logger().info('')
            self.get_logger().info(
                'LATEST SERVO COMMAND vs REAL ROBOT'
            )

            for joint in JOINTS:

                command = self.last_trajectory.get(
                    joint,
                    None
                )

                real = self.real_positions.get(
                    joint,
                    None
                )

                if command is None or real is None:
                    continue

                difference = command - real

                self.get_logger().info(
                    f'{joint}:'
                )

                self.get_logger().info(
                    f'  Servo command: {command:.10f}'
                )

                self.get_logger().info(
                    f'  Real position: {real:.10f}'
                )

                self.get_logger().info(
                    f'  Difference: {difference:.10f} rad'
                )

        self.get_logger().info('-' * 70)


def main(args=None):

    rclpy.init(args=args)

    node = ServoControllerDebug()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    finally:

        node.destroy_node()

        rclpy.shutdown()


if __name__ == '__main__':
    main()