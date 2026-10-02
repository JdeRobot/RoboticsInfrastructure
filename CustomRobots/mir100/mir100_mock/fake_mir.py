#!/usr/bin/env python3
import math

import numpy as np
import rospy
import tf2_msgs.msg
from geometry_msgs.msg import TransformStamped, TwistStamped
from mir_msgs.msg import RobotState
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu, LaserScan

# Room walls in the odom frame, robot starts at the origin
ROOM = (-5.0, 5.0, -4.0, 4.0)

# Sensor mounting in base_footprint, same values as the real MiR100 description
LASERS = {
    "f_scan": ("f_laser_link", 0.4288, 0.2358, math.radians(45)),
    "b_scan": ("b_laser_link", -0.3548, -0.2352, math.radians(-135)),
}
IMU_Z = 0.25
N_SAMPLES = 541
ANGLE_MIN = -math.radians(135)
ANGLE_INC = math.radians(0.5)
RANGE_MIN = 0.05
RANGE_MAX = 29.0


def log(text):
    print(f"[MiR100 mock] {text}", flush=True)


def yaw_to_quat(yaw):
    return 0.0, 0.0, math.sin(yaw / 2), math.cos(yaw / 2)


def transform(parent, child, x, y, z, yaw, stamp):
    t = TransformStamped()
    t.header.stamp = stamp
    t.header.frame_id = parent
    t.child_frame_id = child
    t.transform.translation.x = x
    t.transform.translation.y = y
    t.transform.translation.z = z
    qx, qy, qz, qw = yaw_to_quat(yaw)
    t.transform.rotation.x = qx
    t.transform.rotation.y = qy
    t.transform.rotation.z = qz
    t.transform.rotation.w = qw
    return t


class FakeMir:
    def __init__(self):
        self.x = self.y = self.yaw = 0.0
        self.vx = self.wz = 0.0
        self.last_cmd = rospy.Time(0)

        self.odom_pub = rospy.Publisher("/odom", Odometry, queue_size=10)
        self.odom_enc_pub = rospy.Publisher("/odom_enc", Odometry, queue_size=10)
        self.imu_pub = rospy.Publisher("/imu_data", Imu, queue_size=10)
        self.state_pub = rospy.Publisher("/robot_state", RobotState, queue_size=10)
        self.tf_pub = rospy.Publisher("/tf", tf2_msgs.msg.TFMessage, queue_size=10)
        self.tf_static_pub = rospy.Publisher(
            "/tf_static", tf2_msgs.msg.TFMessage, queue_size=10, latch=True
        )
        self.scan_pubs = {
            name: rospy.Publisher("/" + name, LaserScan, queue_size=10)
            for name in LASERS
        }
        self.scan_pubs["scan"] = rospy.Publisher("/scan", LaserScan, queue_size=10)

        # MiR software 2.7 and newer expects a stamped twist
        rospy.Subscriber("/cmd_vel", TwistStamped, self.cmd_cb, queue_size=1)

        self.publish_static()

    def cmd_cb(self, msg):
        v = msg.twist.linear.x
        w = msg.twist.angular.z
        # Commands arrive many times per second so only changes are logged
        if abs(v - self.vx) > 1e-3 or abs(w - self.wz) > 1e-3:
            log(f"Command received V={v:.2f} m/s W={w:.2f} rad/s")
            if not v and not w:
                self.report_pose("Stopped")
        self.vx = v
        self.wz = w
        self.last_cmd = rospy.Time.now()

    def report_pose(self, text):
        log(f"{text} at x={self.x:.2f} m y={self.y:.2f} m yaw={self.yaw:.2f} rad")

    def publish_static(self):
        now = rospy.Time.now()
        transforms = [transform("base_footprint", "base_link", 0, 0, 0, 0, now)]
        for _, (frame, lx, ly, lyaw) in LASERS.items():
            transforms.append(transform("base_link", frame, lx, ly, 0.1914, lyaw, now))
        transforms.append(transform("base_link", "imu_link", 0, 0, IMU_Z, 0, now))
        self.tf_static_pub.publish(tf2_msgs.msg.TFMessage(transforms))

    def step(self, dt):
        # Same safety behaviour as a real base, stop when commands stop arriving
        if (rospy.Time.now() - self.last_cmd).to_sec() > 0.5:
            if self.vx or self.wz:
                self.vx = self.wz = 0.0
                self.report_pose("No commands for 0.5 s, robot stopped")
        self.x += self.vx * math.cos(self.yaw) * dt
        self.y += self.vx * math.sin(self.yaw) * dt
        self.yaw += self.wz * dt

    def publish_odom(self, now):
        odom = Odometry()
        odom.header.stamp = now
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_footprint"
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        q = yaw_to_quat(self.yaw)
        odom.pose.pose.orientation.x, odom.pose.pose.orientation.y = q[0], q[1]
        odom.pose.pose.orientation.z, odom.pose.pose.orientation.w = q[2], q[3]
        odom.twist.twist.linear.x = self.vx
        odom.twist.twist.angular.z = self.wz
        self.odom_pub.publish(odom)
        self.odom_enc_pub.publish(odom)
        self.tf_pub.publish(
            tf2_msgs.msg.TFMessage(
                [transform("odom", "base_footprint", self.x, self.y, 0, self.yaw, now)]
            )
        )

    def publish_imu(self, now):
        imu = Imu()
        imu.header.stamp = now
        imu.header.frame_id = "imu_link"
        imu.orientation.z, imu.orientation.w = yaw_to_quat(self.yaw)[2:]
        imu.angular_velocity.z = self.wz
        imu.linear_acceleration.z = 9.81
        self.imu_pub.publish(imu)

    def raycast(self, frame_x, frame_y, frame_yaw):
        # Lidar pose in the odom frame
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        ox = self.x + c * frame_x - s * frame_y
        oy = self.y + s * frame_x + c * frame_y
        angles = self.yaw + frame_yaw + ANGLE_MIN + ANGLE_INC * np.arange(N_SAMPLES)
        dx, dy = np.cos(angles), np.sin(angles)
        xmin, xmax, ymin, ymax = ROOM
        with np.errstate(divide="ignore", invalid="ignore"):
            tx = np.where(dx > 0, (xmax - ox) / dx, (xmin - ox) / dx)
            ty = np.where(dy > 0, (ymax - oy) / dy, (ymin - oy) / dy)
        ranges = np.minimum(tx, ty)
        ranges[~np.isfinite(ranges)] = RANGE_MAX
        return np.clip(ranges, RANGE_MIN, RANGE_MAX)

    def publish_scans(self, now):
        for name, (frame, lx, ly, lyaw) in LASERS.items():
            scan = LaserScan()
            scan.header.stamp = now
            scan.header.frame_id = frame
            scan.angle_min = ANGLE_MIN
            scan.angle_max = ANGLE_MIN + ANGLE_INC * (N_SAMPLES - 1)
            scan.angle_increment = ANGLE_INC
            scan.time_increment = 0.0
            scan.scan_time = 0.1
            scan.range_min = RANGE_MIN
            scan.range_max = RANGE_MAX
            scan.ranges = self.raycast(lx, ly, lyaw).tolist()
            self.scan_pubs[name].publish(scan)
            if name == "f_scan":
                self.scan_pubs["scan"].publish(scan)

    def publish_state(self):
        state = RobotState()
        state.robotState = RobotState.ROBOT_STATE_READY
        state.robotStateString = "Ready"
        self.state_pub.publish(state)

    def run(self):
        log("Ready, waiting for commands")
        rate = rospy.Rate(50)
        dt = 1.0 / 50
        tick = 0
        while not rospy.is_shutdown():
            now = rospy.Time.now()
            self.step(dt)
            self.publish_odom(now)
            self.publish_imu(now)
            if tick % 5 == 0:
                self.publish_scans(now)
            if tick % 50 == 0:
                self.publish_state()
                if self.vx or self.wz:
                    self.report_pose("Moving")
            tick += 1
            rate.sleep()


if __name__ == "__main__":
    rospy.init_node("fake_mir")
    FakeMir().run()
