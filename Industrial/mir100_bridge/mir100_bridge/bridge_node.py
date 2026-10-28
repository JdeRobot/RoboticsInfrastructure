#!/usr/bin/env python3
"""ROS2 bridge for the MiR100.

Connects through rosbridge and republishes the robot with the same ROS2 topics
as the simulated one. In robot mode it talks straight to the MiR100, which
already exposes rosbridge. In driver mode it talks to a mir_driver running
outside the docker, with its own rosbridge_server on top.
"""

import math

import rclpy
import roslibpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import Imu, LaserScan

from mir100_bridge.host import resolve_robot_host, resolve_ros1_host

# Maps each ROS1 laser topic to its ROS2 topic and TF frame, matching what
# mir100_common.urdf.xacro gives the simulated robot's lasers
LASER_TOPICS = {
    "f_scan": ("front_laser/scan", "front_laser_link"),
    "b_scan": ("back_laser/scan", "back_laser_link"),
}

# A paused or reset exercise stops sending cmd_vel, but the real robot keeps
# going at the last speed it got, so once commands go quiet for this long we
# stop it ourselves instead of waiting on the robot's own firmware watchdog
COMMAND_TIMEOUT = 0.3


class Mir100Bridge(Node):
    def __init__(self):
        super().__init__("mir100_bridge")

        self.declare_parameter("mode", "robot")
        self.declare_parameter("ros1_hostname", "")
        self.declare_parameter("ros1_port", 0)
        self.declare_parameter("namespace", "mir100")

        mode = self.get_parameter("mode").value
        configured_host = self.get_parameter("ros1_hostname").value
        configured_port = self.get_parameter("ros1_port").value
        self.namespace = self.get_parameter("namespace").value.strip("/")

        if mode == "robot":
            hostname = resolve_robot_host(configured_host)
            port = configured_port or 9090
        elif mode == "driver":
            hostname = resolve_ros1_host(configured_host)
            port = configured_port or 9091
        else:
            raise ValueError(f"unknown mode {mode}, use robot or driver")

        # The MiR software 2.7 and newer expects a stamped twist, mir_driver adds
        # the stamp in driver mode but here nobody does it for us
        self.stamped = mode == "robot"

        self.get_logger().info(
            f"connecting to the MiR100 in {mode} mode at {hostname}:{port}..."
        )
        self.last_cmd_time = self.get_clock().now()
        self.stopped = True

        self.ros1 = roslibpy.Ros(host=hostname, port=port)
        self.ros1.on_ready(self.setup_bridge)
        self.ros1.on("error", lambda e: self.get_logger().warn(f"rosbridge error: {e}"))
        self.ros1.run(timeout=None)  # connects in a background thread without blocking

    def ns(self, topic):
        return f"/{self.namespace}/{topic}"

    def setup_bridge(self):
        self.get_logger().info("connected to ROS1, wiring topics")

        # forward student commands from ROS2 to the ROS1 robot
        cmd_vel_type = (
            "geometry_msgs/TwistStamped" if self.stamped else "geometry_msgs/Twist"
        )
        self.cmd_vel_ros1 = roslibpy.Topic(self.ros1, "/cmd_vel", cmd_vel_type)
        self.create_subscription(Twist, self.ns("cmd_vel"), self.on_cmd_vel, 10)
        self.create_timer(0.1, self.check_command_timeout)

        # republish the robot's ROS1 sensor data as ROS2
        self.odom_pub = self.create_publisher(Odometry, self.ns("odom"), 10)
        roslibpy.Topic(self.ros1, "/odom", "nav_msgs/Odometry").subscribe(self.on_odom)

        self.imu_pub = self.create_publisher(Imu, self.ns("imu"), 10)
        roslibpy.Topic(self.ros1, "/imu_data", "sensor_msgs/Imu").subscribe(self.on_imu)

        self.scan_pubs = {}
        self.scan_frames = {}
        for ros1_topic, (ros2_topic, frame) in LASER_TOPICS.items():
            self.scan_pubs[ros1_topic] = self.create_publisher(
                LaserScan, self.ns(ros2_topic), 10
            )
            self.scan_frames[ros1_topic] = frame
            roslibpy.Topic(
                self.ros1, "/" + ros1_topic, "sensor_msgs/LaserScan"
            ).subscribe(lambda msg, name=ros1_topic: self.on_scan(name, msg))

    def on_cmd_vel(self, msg: Twist):
        self.last_cmd_time = self.get_clock().now()
        self.stopped = False
        self.send_cmd_vel(msg)

    def check_command_timeout(self):
        idle = (self.get_clock().now() - self.last_cmd_time).nanoseconds / 1e9
        if not self.stopped and idle > COMMAND_TIMEOUT:
            self.get_logger().warn("No cmd_vel for a while, stopping the robot")
            self.send_cmd_vel(Twist())
            self.stopped = True

    def send_cmd_vel(self, msg: Twist):
        twist = {
            "linear": {"x": msg.linear.x, "y": msg.linear.y, "z": msg.linear.z},
            "angular": {"x": msg.angular.x, "y": msg.angular.y, "z": msg.angular.z},
        }
        if self.stamped:
            now = self.get_clock().now().nanoseconds
            twist = {
                "header": {
                    "frame_id": "",
                    "stamp": {"secs": now // 10**9, "nsecs": now % 10**9},
                },
                "twist": twist,
            }
        self.cmd_vel_ros1.publish(roslibpy.Message(twist))

    def on_odom(self, msg: dict):
        odom = Odometry()
        odom.header.stamp = self.get_clock().now().to_msg()
        odom.header.frame_id = self.ns("odom").lstrip("/")
        odom.child_frame_id = self.ns("base_footprint").lstrip("/")
        pos = msg["pose"]["pose"]["position"]
        ori = msg["pose"]["pose"]["orientation"]
        odom.pose.pose.position.x = pos["x"]
        odom.pose.pose.position.y = pos["y"]
        odom.pose.pose.position.z = pos["z"]
        odom.pose.pose.orientation.x = ori["x"]
        odom.pose.pose.orientation.y = ori["y"]
        odom.pose.pose.orientation.z = ori["z"]
        odom.pose.pose.orientation.w = ori["w"]
        lin = msg["twist"]["twist"]["linear"]
        ang = msg["twist"]["twist"]["angular"]
        odom.twist.twist.linear.x = lin["x"]
        odom.twist.twist.linear.y = lin["y"]
        odom.twist.twist.angular.z = ang["z"]
        self.odom_pub.publish(odom)

    def on_imu(self, msg: dict):
        imu = Imu()
        imu.header.stamp = self.get_clock().now().to_msg()
        imu.header.frame_id = self.ns("imu_link").lstrip("/")
        ori = msg["orientation"]
        imu.orientation.x = ori["x"]
        imu.orientation.y = ori["y"]
        imu.orientation.z = ori["z"]
        imu.orientation.w = ori["w"]
        av = msg["angular_velocity"]
        imu.angular_velocity.x = av["x"]
        imu.angular_velocity.y = av["y"]
        imu.angular_velocity.z = av["z"]
        la = msg["linear_acceleration"]
        imu.linear_acceleration.x = la["x"]
        imu.linear_acceleration.y = la["y"]
        imu.linear_acceleration.z = la["z"]
        self.imu_pub.publish(imu)

    def on_scan(self, ros1_topic: str, msg: dict):
        scan = LaserScan()
        scan.header.stamp = self.get_clock().now().to_msg()
        scan.header.frame_id = self.ns(self.scan_frames[ros1_topic]).lstrip("/")
        scan.angle_min = msg["angle_min"]
        scan.angle_max = msg["angle_max"]
        scan.angle_increment = msg["angle_increment"]
        scan.time_increment = msg.get("time_increment", 0.0)
        scan.scan_time = msg.get("scan_time", 0.0)
        scan.range_min = msg["range_min"]
        scan.range_max = msg["range_max"]
        scan.ranges = [
            r if r is not None and not math.isnan(r) else msg["range_max"]
            for r in msg["ranges"]
        ]
        scan.intensities = list(msg.get("intensities", []))
        self.scan_pubs[ros1_topic].publish(scan)

    def destroy_node(self):
        if self.ros1.is_connected:
            self.ros1.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = Mir100Bridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
