import time
import math
import rclpy

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import String
from rclpy.qos import QoSProfile, QoSDurabilityPolicy

CAR_NAMESPACE = "car"
CMD_VEL_TOPIC = "/" + CAR_NAMESPACE + "/cmd_vel"
ODOM_TOPIC = "/" + CAR_NAMESPACE + "/odom"
TRACK_TOPIC = "/visual_lander/track"

DEFAULT_TRACK = "shuttle"
TRACK_TIMEOUT = 10.0

# Each track is a loop of (x, y, speed) waypoints, driven with a heading P-controller.
TRACKS = {
    "shuttle": [
        (-12.0, 0.0, 1.5),
        (12.0, 0.0, 1.5),
    ],
    "circuit": [
        (-6.0, -15.0, 1.5),
        (6.0, -15.0, 1.5),
        (15.0, -6.0, 1.0),
        (15.0, 6.0, 1.5),
        (6.0, 15.0, 1.0),
        (-6.0, 15.0, 1.5),
        (-15.0, 6.0, 1.0),
        (-15.0, -6.0, 1.0),
    ],
}

WAYPOINT_RADIUS = 1.0
KP_YAW = 2.0
MAX_YAW_RATE = 1.5

# A jump this big in one tick means RAM just reset the world, not real motion.
RESET_JUMP_DISTANCE = 3.0

if not rclpy.ok():
    rclpy.init()

node = rclpy.create_node("visual_lander_car")
cmd_pub = node.create_publisher(Twist, CMD_VEL_TOPIC, 10)

car_pose = [0.0, 0.0, 0.0]  # x, y, yaw
last_pose = None
track_name = None


def odom_callback(msg):
    car_pose[0] = msg.pose.pose.position.x
    car_pose[1] = msg.pose.pose.position.y
    q = msg.pose.pose.orientation
    car_pose[2] = math.atan2(
        2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    )


def track_callback(msg):
    global track_name
    track_name = msg.data


node.create_subscription(Odometry, ODOM_TOPIC, odom_callback, 10)
# Latched by the world launcher, so it arrives however late this starts
node.create_subscription(
    String,
    TRACK_TOPIC,
    track_callback,
    QoSProfile(depth=1, durability=QoSDurabilityPolicy.TRANSIENT_LOCAL),
)


def get_track():
    give_up_at = time.time() + TRACK_TIMEOUT
    while track_name is None and time.time() < give_up_at:
        rclpy.spin_once(node, timeout_sec=0.05)
    return TRACKS.get(track_name, TRACKS[DEFAULT_TRACK])


def wrap(angle):
    return (angle + math.pi) % (2 * math.pi) - math.pi


def clamp(value, limit):
    return max(-limit, min(limit, value))


waypoints = get_track()
print("car driving the %s track" % (track_name or DEFAULT_TRACK), flush=True)
target_index = 0

while rclpy.ok():
    rclpy.spin_once(node, timeout_sec=0)

    if last_pose is not None:
        jump = math.hypot(car_pose[0] - last_pose[0], car_pose[1] - last_pose[1])
        if jump > RESET_JUMP_DISTANCE:
            target_index = 0
    last_pose = (car_pose[0], car_pose[1])

    target_x, target_y, speed = waypoints[target_index]
    dx = target_x - car_pose[0]
    dy = target_y - car_pose[1]
    distance = math.hypot(dx, dy)

    if distance < WAYPOINT_RADIUS:
        target_index = (target_index + 1) % len(waypoints)

    heading_error = wrap(math.atan2(dy, dx) - car_pose[2])

    twist = Twist()
    twist.linear.x = speed
    twist.angular.z = clamp(KP_YAW * heading_error, MAX_YAW_RATE)
    cmd_pub.publish(twist)

    time.sleep(0.05)
