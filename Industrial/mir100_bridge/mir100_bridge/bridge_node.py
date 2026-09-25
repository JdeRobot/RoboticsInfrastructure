#!/usr/bin/env python3
"""ROS1 to ROS2 bridge node for the MiR100.

Connects, as a plain rosbridge websocket client, to the ROS1 side the student
already has running (mir_driver, talking to the real or mocked robot) with
rosbridge_server on top of it. No ROS1 install is needed here, only the
websocket protocol, so this node is pure ROS2/rclpy and lives inside the
RoboticsAcademy docker like any other exercise node.

Topic names on the ROS2 side match the ones the simulated MiR100 already
publishes (see CustomRobots/mir100/launch/mir100.launch.py), so the HAL sees
no difference between sim and real robot.
"""

import math

import rclpy
import roslibpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import Imu, LaserScan

# Maps each ROS1 laser topic to its ROS2 topic and TF frame, matching what
# mir100_common.urdf.xacro gives the simulated robot's lasers
LASER_TOPICS = {
    "f_scan": ("front_laser/scan", "front_laser_link"),
    "b_scan": ("back_laser/scan", "back_laser_link"),
}


class Mir100Bridge(Node):
    def __init__(self):
        super().__init__("mir100_bridge")

        self.declare_parameter("ros1_hostname", "localhost")
        self.declare_parameter("ros1_port", 9091)
        self.declare_parameter("namespace", "mir100")

        hostname = self.get_parameter("ros1_hostname").value
        port = self.get_parameter("ros1_port").value
        self.namespace = self.get_parameter("namespace").value.strip("/")

        self.get_logger().info(f"connecting to ROS1 rosbridge at {hostname}:{port}...")
        self.ros1 = roslibpy.Ros(host=hostname, port=port)
        self.ros1.on_ready(self.setup_bridge)
        self.ros1.on("error", lambda e: self.get_logger().warn(f"rosbridge error: {e}"))
        self.ros1.run(timeout=None)  # connects in a background thread, non-blocking

    def ns(self, topic):
        return f"/{self.namespace}/{topic}"

    def setup_bridge(self):
        self.get_logger().info("connected to ROS1, wiring topics")

        # forward student commands from ROS2 to the ROS1 robot
        self.cmd_vel_ros1 = roslibpy.Topic(self.ros1, "/cmd_vel", "geometry_msgs/Twist")
        self.create_subscription(Twist, self.ns("cmd_vel"), self.on_cmd_vel, 10)

        # republish the robot's ROS1 sensor data as ROS2
        self.odom_pub = self.create_publisher(Odometry, self.ns("odom"), 10)
        roslibpy.Topic(self.ros1, "/odom", "nav_msgs/Odometry").subscribe(self.on_odom)

        self.imu_pub = self.create_publisher(Imu, self.ns("imu"), 10)
        roslibpy.Topic(self.ros1, "/imu_data", "sensor_msgs/Imu").subscribe(self.on_imu)

        self.scan_pubs = {}
        self.scan_frames = {}
        for ros1_topic, (ros2_topic, frame) in LASER_TOPICS.items():
            self.scan_pubs[ros1_topic] = self.create_publisher(LaserScan, self.ns(ros2_topic), 10)
            self.scan_frames[ros1_topic] = frame
            roslibpy.Topic(self.ros1, "/" + ros1_topic, "sensor_msgs/LaserScan").subscribe(
                lambda msg, name=ros1_topic: self.on_scan(name, msg)
            )

    def on_cmd_vel(self, msg: Twist):
        self.cmd_vel_ros1.publish(
            roslibpy.Message(
                {
                    "linear": {"x": msg.linear.x, "y": msg.linear.y, "z": msg.linear.z},
                    "angular": {"x": msg.angular.x, "y": msg.angular.y, "z": msg.angular.z},
                }
            )
        )

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
