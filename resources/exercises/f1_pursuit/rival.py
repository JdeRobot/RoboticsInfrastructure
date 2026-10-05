import math
import sys
import threading
import time

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.executors import MultiThreadedExecutor
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import Bool

sys.path.insert(0, "/workspace/code")

freq = 30.0

RIVAL_NAMESPACE = "f1_rival"
CHASER_NAMESPACE = "f1"

CATCH_RADIUS = 2.5
ARM_GAP = 4.0

### HAL INIT ###

if not rclpy.ok():
    rclpy.init()

CAM_TOPIC = "/" + RIVAL_NAMESPACE + "/camera/image_raw"
CMD_TOPIC = "/" + RIVAL_NAMESPACE + "/cmd_vel"
ODOM_TOPIC = "/" + RIVAL_NAMESPACE + "/odom"
CHASER_ODOM_TOPIC = "/" + CHASER_NAMESPACE + "/odom"

bridge = CvBridge()
executor = MultiThreadedExecutor()
node = rclpy.create_node("f1_rival_node")

image = [None]
pose = [0.0, 0.0, 0.0]
yaw = [0.0]
chaser = [0.0, 0.0, 0.0]


def image_callback(msg):
    try:
        image[0] = bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
    except Exception:
        pass


def quat2Yaw(q):
    return math.atan2(
        2.0 * (q.x * q.y + q.w * q.z), q.w * q.w + q.x * q.x - q.y * q.y - q.z * q.z
    )


def odom_callback(msg):
    p = msg.pose.pose.position
    pose[0], pose[1], pose[2] = p.x, p.y, p.z
    yaw[0] = quat2Yaw(msg.pose.pose.orientation)


def chaser_callback(msg):
    p = msg.pose.pose.position
    chaser[0], chaser[1], chaser[2] = p.x, p.y, p.z


node.create_subscription(Image, CAM_TOPIC, image_callback, qos_profile_sensor_data)
node.create_subscription(Odometry, ODOM_TOPIC, odom_callback, qos_profile_sensor_data)
node.create_subscription(
    Odometry, CHASER_ODOM_TOPIC, chaser_callback, qos_profile_sensor_data
)

cmd_pub = node.create_publisher(Twist, CMD_TOPIC, 10)
armed_pub = node.create_publisher(
    Bool,
    "/f1_pursuit/armed",
    QoSProfile(depth=1, durability=QoSDurabilityPolicy.TRANSIENT_LOCAL),
)

executor.add_node(node)


def __auto_spin() -> None:
    while rclpy.ok():
        try:
            executor.spin_once(timeout_sec=0)
        except Exception:
            pass
        time.sleep(1 / freq)


executor_thread = threading.Thread(target=__auto_spin, daemon=True)
executor_thread.start()


### LINE DETECTION ###

ROWS = (0.88, 0.80, 0.72, 0.63, 0.54)
MIN_RUN = 3


def red_mask(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # Red wraps the hue origin, so it takes two ranges
    return cv2.inRange(hsv, (0, 110, 70), (10, 255, 255)) | cv2.inRange(
        hsv, (170, 110, 70), (180, 255, 255)
    )


def row_runs(row):
    hits = np.flatnonzero(row)
    if hits.size < MIN_RUN:
        return []
    splits = np.flatnonzero(np.diff(hits) > 1)
    return [(r.mean(), r.size) for r in np.split(hits, splits + 1) if r.size >= MIN_RUN]


def follow_line(mask, seed):
    
    h, w = mask.shape[:2]
    columns = []
    anchor = seed
    for frac in ROWS:
        runs = row_runs(mask[int(h * frac), :])
        if not runs:
            columns.append(None)
            continue
        best = min(runs, key=lambda r: abs(r[0] - anchor))
        if columns and columns[0] is not None and abs(best[0] - anchor) > w * 0.45:
            columns.append(None)
            continue
        anchor = best[0]
        columns.append(best[0])
    return columns


### CONTROL ###

V_MAX = 3.4
V_MIN = 1.2
RUBBER = 0.25

KP = 1.35
KI = 0.12
KD = 0.55
K_CURVE = 0.9
I_CLAMP = 0.4
W_CLAMP = 1.6

CORNER_BRAKE = 1.5
TARGET_GAP = 5.0
RUBBER_SPAN = 14.0


def clamp(value, low, high):
    return max(low, min(high, value))


def dist_xy(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def set_cmd(v, w):
    msg = Twist()
    msg.linear.x = float(v)
    msg.angular.z = float(w)
    cmd_pub.publish(msg)


def publish_armed(value):
    msg = Bool()
    msg.data = bool(value)
    armed_pub.publish(msg)


publish_armed(False)
print("rival away, catch it", flush=True)

armed = False
caught = False
stopped = False
track_x = None
integral = 0.0
last_error = 0.0
last_time = time.time()
speed = 0.0

while rclpy.ok():
    now = time.time()
    dt = clamp(now - last_time, 1e-3, 0.2)
    last_time = now

    chaser_known = any(abs(c) > 1e-6 for c in chaser)
    gap = dist_xy(pose, chaser) if chaser_known else 1e9

    if not armed and chaser_known and gap > ARM_GAP:
        armed = True
        publish_armed(True)
        print("clear by %.1f m, the chase is on" % gap, flush=True)

    if not caught and armed and chaser_known and gap < CATCH_RADIUS:
        caught = True
        print("", flush=True)
        print("CAUGHT", flush=True)
        print("", flush=True)

    if caught:
        if not stopped:
            set_cmd(0.0, 0.0)
            stopped = True
        time.sleep(0.05)
        continue

    img = image[0]
    if img is None:
        time.sleep(1 / freq)
        continue

    h, w = img.shape[:2]
    mask = red_mask(img)
    if track_x is None:
        track_x = w / 2.0

    columns = follow_line(mask, track_x)
    near = columns[0]

    if near is None:
        side = 1.0 if track_x < w / 2.0 else -1.0
        set_cmd(V_MIN * 0.5, side * 0.7)
        integral = 0.0
        time.sleep(1 / freq)
        continue

    track_x = near
    error = (near - w / 2.0) / (w / 2.0)
    far = next((c for c in reversed(columns) if c is not None), near)
    curve = (far - near) / (w / 2.0)

    integral = clamp(integral + error * dt, -I_CLAMP, I_CLAMP)
    derivative = (error - last_error) / dt
    last_error = error

    steer = -(KP * error + KI * integral + KD * derivative * 0.1 + K_CURVE * curve)
    steer = clamp(steer, -W_CLAMP, W_CLAMP)

    bend = clamp(abs(curve) * CORNER_BRAKE + 0.4 * abs(error), 0.0, 1.0)
    target = V_MAX - (V_MAX - V_MIN) * bend

    if armed and chaser_known:
        to_chaser = math.atan2(chaser[1] - pose[1], chaser[0] - pose[0])
        bearing = (to_chaser - yaw[0] + math.pi) % (2 * math.pi) - math.pi
        if abs(bearing) > math.pi / 2:
            if gap > TARGET_GAP:
                slack = clamp((gap - TARGET_GAP) / RUBBER_SPAN, 0.0, 1.0)
                target -= (V_MAX - V_MIN) * RUBBER * slack
        else:
            target = V_MAX

    target = clamp(target, V_MIN, V_MAX)
    speed += clamp(target - speed, -6.0 * dt, 4.0 * dt)

    set_cmd(speed, steer)
    time.sleep(1 / freq)
