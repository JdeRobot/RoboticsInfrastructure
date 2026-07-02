#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from trajectory_msgs.msg import JointTrajectory


class TrajectoryRelay(Node):

    def __init__(self):
        super().__init__("trajectory_relay")

        self.publisher = self.create_publisher(
            JointTrajectory,
            "/scaled_joint_trajectory_controller/joint_trajectory",
            10,
        )

        self.subscription = self.create_subscription(
            JointTrajectory,
            "/joint_trajectory_controller/joint_trajectory",
            self.callback,
            10,
        )

        self.get_logger().info("Trajectory relay started")


    def callback(self, msg):
        self.get_logger().info(
            f"Relaying trajectory with {len(msg.points)} points"
        )

        self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)

    node = TrajectoryRelay()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == "__main__":
    main()
