#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry

NAMESPACE = "turtlebot3"

# Loop track from Scenes/follow_turtlebot.world, clockwise starting at
# waypoint_1. Each entry is (x, y, speed), speed is the linear speed used
# while heading toward that point, slow through the cone slalom and the
# bridge, fast on the two open straights.
SPEED_FAST = 0.7
SPEED_SLALOM = 0.3
SPEED_BRIDGE = 0.4

WAYPOINTS = [
    (7.0, -4.0, SPEED_FAST),     # waypoint_1, slalom entry
    (4.0, -2.8, SPEED_SLALOM),   # past cone_1, north side
    (1.0, -5.2, SPEED_SLALOM),   # past cone_2, south side
    (-2.0, -2.8, SPEED_SLALOM),  # past cone_3, north side
    (-5.0, -5.2, SPEED_SLALOM),  # past cone_4, south side
    (-7.0, -4.0, SPEED_FAST),    # waypoint_2, slalom exit
    (-7.0, 4.0, SPEED_FAST),     # waypoint_3, west straight
    (-2.0, 4.0, SPEED_BRIDGE),   # bridge approach
    (2.0, 4.0, SPEED_BRIDGE),    # bridge exit
    (7.0, 4.0, SPEED_FAST),      # waypoint_4, east straight back to start
]

ANGULAR_SPEED = 1.2
DISTANCE_TOLERANCE = 0.25
KP_ANGULAR = 1.5
KD_ANGULAR = 0.3
CONTROL_PERIOD = 0.1


def yaw_from_quaternion(q):
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


def wrap_angle(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


class TurtlebotPatrol(Node):
    def __init__(self):
        super().__init__("turtlebot_patrol")

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.have_odom = False
        self.target_index = 0
        self.prev_angle_error = 0.0

        self.cmd_pub = self.create_publisher(Twist, f"/{NAMESPACE}/cmd_vel", 10)
        self.create_subscription(
            Odometry, f"/{NAMESPACE}/odom", self.odom_callback, 10
        )
        self.create_timer(0.1, self.control_loop)

    def odom_callback(self, msg):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        self.yaw = yaw_from_quaternion(msg.pose.pose.orientation)
        self.have_odom = True

    def control_loop(self):
        if not self.have_odom:
            return

        target_x, target_y, speed = WAYPOINTS[self.target_index]
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)

        if distance < DISTANCE_TOLERANCE:
            self.target_index = (self.target_index + 1) % len(WAYPOINTS)
            self.prev_angle_error = 0.0
            return

        angle_error = wrap_angle(math.atan2(dy, dx) - self.yaw)
        angle_error_rate = wrap_angle(angle_error - self.prev_angle_error) / CONTROL_PERIOD
        self.prev_angle_error = angle_error

        cmd = Twist()
        cmd.linear.x = speed * max(0.0, math.cos(angle_error))
        cmd.angular.z = max(
            -ANGULAR_SPEED,
            min(ANGULAR_SPEED, KP_ANGULAR * angle_error + KD_ANGULAR * angle_error_rate),
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
