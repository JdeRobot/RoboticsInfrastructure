#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import JointState
from geometry_msgs.msg import TwistStamped
from trajectory_msgs.msg import JointTrajectory
from control_msgs.msg import JointTrajectoryControllerState

import math
import time


class ServoChainDebug(Node):

    def __init__(self):

        super().__init__('servo_chain_debug')

        self.start_time = time.time()

        self.joint_names = [
            'shoulder_pan_joint',
            'shoulder_lift_joint',
            'elbow_joint',
            'wrist_1_joint',
            'wrist_2_joint',
            'wrist_3_joint'
        ]

        # ==========================================================
        # DATA
        # ==========================================================

        self.current_joints = {}
        self.start_servo_joints = None

        self.last_twist = None
        self.last_trajectory = None
        self.last_controller = None

        self.servo_started = False

        self.twist_count = 0
        self.trajectory_count = 0
        self.joint_state_count = 0
        self.controller_count = 0

        # Maximum values
        self.max_twist = 0.0
        self.max_commanded_delta = 0.0
        self.max_real_delta = 0.0
        self.max_controller_error = 0.0

        # ==========================================================
        # SUBSCRIBERS
        # ==========================================================

        self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            100
        )

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
            100
        )

        self.create_subscription(
            JointTrajectoryControllerState,
            '/joint_trajectory_controller/state',
            self.controller_callback,
            100
        )

        # ==========================================================
        # TIMER
        # ==========================================================

        self.create_timer(
            1.0,
            self.print_status
        )

        self.get_logger().info('')
        self.get_logger().info('==================================================')
        self.get_logger().info('MOVEIT SERVO CHAIN DEBUG')
        self.get_logger().info('==================================================')
        self.get_logger().info('')
        self.get_logger().info('Run your HAL program now.')
        self.get_logger().info('')
        self.get_logger().info('This node compares:')
        self.get_logger().info('Twist -> Servo trajectory -> Controller -> Robot')
        self.get_logger().info('')
        self.get_logger().info('==================================================')

    # ==============================================================
    # JOINT STATES
    # ==============================================================

    def joint_state_callback(self, msg):

        self.joint_state_count += 1

        for name, position in zip(msg.name, msg.position):

            if name in self.joint_names:

                self.current_joints[name] = position

        # Detect first Servo movement

        if self.servo_started and self.start_servo_joints is None:

            if len(self.current_joints) == 6:

                self.start_servo_joints = dict(self.current_joints)

                self.get_logger().info('')
                self.get_logger().info('[SERVO START POSITION]')
                self.print_joint_dict(
                    self.start_servo_joints
                )

        # Calculate real movement

        if self.start_servo_joints is not None:

            for name in self.joint_names:

                if (
                    name in self.current_joints and
                    name in self.start_servo_joints
                ):

                    delta = abs(
                        self.current_joints[name] -
                        self.start_servo_joints[name]
                    )

                    if delta > self.max_real_delta:

                        self.max_real_delta = delta

    # ==============================================================
    # TWIST
    # ==============================================================

    def twist_callback(self, msg):

        self.twist_count += 1

        linear_mag = math.sqrt(
            msg.twist.linear.x ** 2 +
            msg.twist.linear.y ** 2 +
            msg.twist.linear.z ** 2
        )

        angular_mag = math.sqrt(
            msg.twist.angular.x ** 2 +
            msg.twist.angular.y ** 2 +
            msg.twist.angular.z ** 2
        )

        magnitude = linear_mag + angular_mag

        if magnitude > 0.000001:

            if not self.servo_started:

                self.servo_started = True

                self.get_logger().info('')
                self.get_logger().info('==================================================')
                self.get_logger().info('[SERVO COMMAND DETECTED]')
                self.get_logger().info('==================================================')

            self.max_twist = max(
                self.max_twist,
                magnitude
            )

            self.last_twist = msg

    # ==============================================================
    # TRAJECTORY
    # ==============================================================

    def trajectory_callback(self, msg):

        self.trajectory_count += 1

        if len(msg.points) == 0:
            return

        if len(msg.points[0].positions) == 0:
            return

        positions = msg.points[0].positions

        trajectory_dict = {}

        for name, position in zip(
            msg.joint_names,
            positions
        ):

            if name in self.joint_names:

                trajectory_dict[name] = position

        self.last_trajectory = trajectory_dict

        # Compare trajectory target with current position

        if len(self.current_joints) > 0:

            for name in self.joint_names:

                if (
                    name in trajectory_dict and
                    name in self.current_joints
                ):

                    delta = abs(
                        trajectory_dict[name] -
                        self.current_joints[name]
                    )

                    if delta > self.max_commanded_delta:

                        self.max_commanded_delta = delta

    # ==============================================================
    # CONTROLLER STATE
    # ==============================================================

    def controller_callback(self, msg):

        self.controller_count += 1

        self.last_controller = msg

        # Modern controller state message

        try:

            desired = msg.reference.positions
            actual = msg.feedback.positions

            if (
                len(desired) > 0 and
                len(actual) > 0
            ):

                for d, a in zip(desired, actual):

                    error = abs(d - a)

                    if error > self.max_controller_error:

                        self.max_controller_error = error

        except Exception:

            pass

    # ==============================================================
    # PRINT STATUS
    # ==============================================================

    def print_status(self):

        elapsed = time.time() - self.start_time

        self.get_logger().info('')
        self.get_logger().info('--------------------------------------------------')
        self.get_logger().info(
            f'TIME: {elapsed:.1f} s'
        )

        self.get_logger().info('')
        self.get_logger().info(
            f'joint_states: {self.joint_state_count}'
        )

        self.get_logger().info(
            f'Twist commands: {self.twist_count}'
        )

        self.get_logger().info(
            f'Trajectories: {self.trajectory_count}'
        )

        self.get_logger().info(
            f'Controller states: {self.controller_count}'
        )

        self.get_logger().info('')
        self.get_logger().info(
            f'Max Twist magnitude: '
            f'{self.max_twist:.8f}'
        )

        self.get_logger().info(
            f'Max commanded joint delta: '
            f'{self.max_commanded_delta:.10f} rad'
        )

        self.get_logger().info(
            f'Max real joint movement: '
            f'{self.max_real_delta:.10f} rad'
        )

        self.get_logger().info(
            f'Max controller error: '
            f'{self.max_controller_error:.10f} rad'
        )

        # ==========================================================
        # CURRENT TWIST
        # ==========================================================

        if self.last_twist is not None:

            msg = self.last_twist

            self.get_logger().info('')
            self.get_logger().info('[LAST TWIST]')

            self.get_logger().info(
                f'Frame: {msg.header.frame_id}'
            )

            self.get_logger().info(
                f'Linear: '
                f'[{msg.twist.linear.x:.8f}, '
                f'{msg.twist.linear.y:.8f}, '
                f'{msg.twist.linear.z:.8f}]'
            )

            self.get_logger().info(
                f'Angular: '
                f'[{msg.twist.angular.x:.8f}, '
                f'{msg.twist.angular.y:.8f}, '
                f'{msg.twist.angular.z:.8f}]'
            )

        # ==========================================================
        # CURRENT TRAJECTORY
        # ==========================================================

        if self.last_trajectory is not None:

            self.get_logger().info('')
            self.get_logger().info('[LAST SERVO TRAJECTORY]')

            for name in self.joint_names:

                if (
                    name in self.last_trajectory and
                    name in self.current_joints
                ):

                    target = self.last_trajectory[name]

                    current = self.current_joints[name]

                    delta = target - current

                    self.get_logger().info(
                        f'{name}: '
                        f'current={current:.8f} '
                        f'target={target:.8f} '
                        f'delta={delta:.10f}'
                    )

    # ==============================================================
    # PRINT JOINT DICTIONARY
    # ==============================================================

    def print_joint_dict(self, data):

        for name in self.joint_names:

            if name in data:

                self.get_logger().info(
                    f'{name}: {data[name]:.8f}'
                )


def main(args=None):

    rclpy.init(args=args)

    node = ServoChainDebug()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':

    main()