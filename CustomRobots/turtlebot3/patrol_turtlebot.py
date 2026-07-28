#!/usr/bin/env python3

import math
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry

NAMESPACE = "turtlebot3"

# Same order as the numbered pads in follow_turtlebot.world
WAYPOINTS = [
    (4.0, 2.5),
    (4.0, -2.5),
    (-4.0, -2.5),
    (-4.0, 2.5),
]

LINEAR_SPEED = 0.25
ANGULAR_SPEED = 0.6
DISTANCE_TOLERANCE = 0.25
ANGLE_TOLERANCE = 0.15
KP_ANGULAR = 1.5


def yaw_from_quaternion(q):
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


def wrap_angle(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


class TurtlebotPatrol(Node):
    def __init__(self):
        super().__init__("turtlebot_patrol")

        # Give the turtlebot3 bridge time to come up so odom is not stale from the start
        time.sleep(5)

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.target_index = 0

        self.cmd_pub = self.create_publisher(
            Twist, f"/{NAMESPACE}/cmd_vel", 10
        )
        self.create_subscription(
            Odometry, f"/{NAMESPACE}/odom", self.odom_callback, 10
        )
        self.create_timer(0.1, self.control_loop)

    def odom_callback(self, msg):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        self.yaw = yaw_from_quaternion(msg.pose.pose.orientation)

    def control_loop(self):
        target_x, target_y = WAYPOINTS[self.target_index]
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)

        if distance < DISTANCE_TOLERANCE:
            self.target_index = (self.target_index + 1) % len(WAYPOINTS)
            return

        angle_error = wrap_angle(math.atan2(dy, dx) - self.yaw)

        cmd = Twist()
        if abs(angle_error) > ANGLE_TOLERANCE:
            cmd.linear.x = 0.0
        else:
            cmd.linear.x = LINEAR_SPEED
        cmd.angular.z = max(
            -ANGULAR_SPEED, min(ANGULAR_SPEED, KP_ANGULAR * angle_error)
        )
        self.cmd_pub.publish(cmd)


def main():
    rclpy.init()
    node = TurtlebotPatrol()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
