import json
import math
import os
import threading
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, qos_profile_sensor_data
from rosgraph_msgs.msg import Clock
from std_msgs.msg import String

freq = 30.0

RIVAL_NAMESPACE = "f1_rival"
CHASER_NAMESPACE = "f1"

DEFAULT_LEVEL = "medium"
LEVEL_TIMEOUT = 10.0

# Top speed, corner speed and lateral grip of the rival on each level
LEVELS = {
    "easy": {"V_MAX": 4.0, "V_MIN": 2.5, "A_LAT": 2.0},
    "medium": {"V_MAX": 6.0, "V_MIN": 3.5, "A_LAT": 3.0},
    "hard": {"V_MAX": 8.0, "V_MIN": 4.5, "A_LAT": 4.0},
}

# The chase is lost once the rival has driven this many laps
RIVAL_LAPS = 2

BRAKE = 3.0
CATCH_GAP = 1.5
CATCH_RADIUS = 2.0
SEARCH_WINDOW = 15

CENTERLINE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "simple_circuit_centerline.csv"
)

### NODE ###

if not rclpy.ok():
    rclpy.init()

node = rclpy.create_node("f1_pursuit_rival")
executor = rclpy.executors.MultiThreadedExecutor()

latched = QoSProfile(depth=1, durability=QoSDurabilityPolicy.TRANSIENT_LOCAL)

rival = [None]
chaser = [None]
sim_time = [None]
level = [None]


def pose_from(msg):
    p = msg.pose.pose.position
    q = msg.pose.pose.orientation
    yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))
    return (p.x, p.y, yaw)


def rival_callback(msg):
    rival[0] = pose_from(msg)


def chaser_callback(msg):
    chaser[0] = pose_from(msg)


def clock_callback(msg):
    sim_time[0] = msg.clock.sec + msg.clock.nanosec * 1e-9


def level_callback(msg):
    level[0] = msg.data


node.create_subscription(
    Odometry, "/" + RIVAL_NAMESPACE + "/odom", rival_callback, qos_profile_sensor_data
)
node.create_subscription(
    Odometry,
    "/" + CHASER_NAMESPACE + "/odom",
    chaser_callback,
    qos_profile_sensor_data,
)
node.create_subscription(Clock, "/clock", clock_callback, qos_profile_sensor_data)
# Latched by the world launcher, so it arrives however late this starts
node.create_subscription(String, "/f1_pursuit/level", level_callback, latched)

cmd_pub = node.create_publisher(Twist, "/" + RIVAL_NAMESPACE + "/cmd_vel", 10)
status_pub = node.create_publisher(String, "/f1_pursuit/status", latched)

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

### TRACK ###


def load_track():
    points = []
    with open(CENTERLINE) as track_file:
        for line in track_file:
            if line.startswith("#") or not line.strip():
                continue
            x, y = line.split(",")
            points.append((float(x), float(y)))
    stations = [0.0]
    for i in range(1, len(points)):
        stations.append(stations[-1] + math.dist(points[i - 1], points[i]))
    return points, stations, stations[-1] + math.dist(points[-1], points[0])


TRACK, STATIONS, LAP = load_track()
N = len(TRACK)


def curvature(i):
    a, b, c = TRACK[i - 3], TRACK[i], TRACK[(i + 3) % N]
    cross = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
    sides = math.dist(a, b) * math.dist(b, c) * math.dist(c, a)
    return 2.0 * cross / sides if sides > 1e-9 else 0.0


def speed_profile(cfg):
    speeds = []
    for i in range(N):
        bend = max(curvature(i), 1e-6)
        speeds.append(
            min(cfg["V_MAX"], max(cfg["V_MIN"], math.sqrt(cfg["A_LAT"] / bend)))
        )
    # Brake ahead of every corner, twice round so the lap wraps cleanly
    for _ in range(2):
        for i in range(N - 1, -1, -1):
            step = math.dist(TRACK[i], TRACK[(i + 1) % N])
            reachable = math.sqrt(speeds[(i + 1) % N] ** 2 + 2.0 * BRAKE * step)
            speeds[i] = min(speeds[i], reachable)
    return speeds


def nearest(x, y, hint=None):
    if hint is None:
        candidates = range(N)
    else:
        candidates = (
            i % N for i in range(hint - SEARCH_WINDOW, hint + SEARCH_WINDOW + 1)
        )
    return min(
        candidates, key=lambda i: (TRACK[i][0] - x) ** 2 + (TRACK[i][1] - y) ** 2
    )


def station(x, y, i):
    # Projects the car onto the segment that leaves point i
    a, b = TRACK[i], TRACK[(i + 1) % N]
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    t = ((x - a[0]) * dx + (y - a[1]) * dy) / (length * length)
    return STATIONS[i] + max(-1.0, min(1.0, t)) * length


class Progress:
    """Distance driven along the track, unwrapped so laps keep adding up"""

    def __init__(self, x, y, start):
        self.index = nearest(x, y)
        local = station(x, y, self.index)
        # Start is the station the car is meant to be at, which fixes the lap count
        self.total = start + wrap_lap(local - start)
        self.local = local

    def update(self, x, y):
        self.index = nearest(x, y, self.index)
        local = station(x, y, self.index)
        self.total += wrap_lap(local - self.local)
        self.local = local
        return self.total


def wrap_lap(delta):
    return (delta + LAP / 2.0) % LAP - LAP / 2.0


### RACE ###


def set_cmd(v, w):
    msg = Twist()
    msg.linear.x = float(v)
    msg.angular.z = float(w)
    cmd_pub.publish(msg)


def publish_status(state, elapsed, gap):
    msg = String()
    msg.data = json.dumps(
        {
            "state": state,
            "level": level_name,
            "elapsed": round(elapsed, 2),
            "limit": round(limit, 2),
            "gap": round(gap, 2),
        }
    )
    status_pub.publish(msg)


def now():
    return sim_time[0] if sim_time[0] is not None else time.time()


def score_for(seconds):
    return max(10, int(round(100 * (1.0 - seconds / limit))))


waited = time.time()
while level[0] is None and time.time() - waited < LEVEL_TIMEOUT:
    time.sleep(0.05)
level_name = level[0] if level[0] in LEVELS else DEFAULT_LEVEL

SPEEDS = speed_profile(LEVELS[level_name])
rival_lap = sum(math.dist(TRACK[i], TRACK[(i + 1) % N]) / SPEEDS[i] for i in range(N))
limit = RIVAL_LAPS * rival_lap

while rival[0] is None or chaser[0] is None:
    time.sleep(0.05)

rival_progress = Progress(rival[0][0], rival[0][1], LAP / 2.0)
chaser_progress = Progress(chaser[0][0], chaser[0][1], 0.0)
start = now()
state = "racing"
stopped = False
last_status = 0.0

print(
    "rival away on the %s level, catch it before it drives %d laps (%.0f s)"
    % (level_name, RIVAL_LAPS, limit),
    flush=True,
)

while rclpy.ok():
    x, y, yaw = rival[0]
    cx, cy, _ = chaser[0]
    rival_s = rival_progress.update(x, y)
    chaser_s = chaser_progress.update(cx, cy)
    if state == "racing":
        gap = rival_s - chaser_s
        elapsed = now() - start

        # Measured along the track, so a car across the infield never counts
        if gap < CATCH_GAP and math.hypot(x - cx, y - cy) < CATCH_RADIUS:
            state = "caught"
            print("", flush=True)
            print("CAUGHT in %.1f seconds" % elapsed, flush=True)
            print("SCORE %d out of 100" % score_for(elapsed), flush=True)
            print("", flush=True)
        elif elapsed > limit:
            state = "escaped"
            print("", flush=True)
            print("ESCAPED, the rival finished %d laps" % RIVAL_LAPS, flush=True)
            print("it was still %.1f m ahead" % gap, flush=True)
            print("SCORE 0 out of 100", flush=True)
            print("", flush=True)

    if time.time() - last_status > 0.1 or state != "racing":
        publish_status(state, elapsed, gap)
        last_status = time.time()

    if state != "racing":
        if not stopped:
            set_cmd(0.0, 0.0)
            stopped = True
        time.sleep(0.1)
        continue

    # Pure pursuit on the red line, the lookahead grows with speed
    i = rival_progress.index
    speed = SPEEDS[i]
    lookahead = max(2.0, 0.6 * speed)
    target = i
    while math.dist(TRACK[target % N], (x, y)) < lookahead and target - i < N // 4:
        target += 1
    tx, ty = TRACK[target % N]
    alpha = math.atan2(ty - y, tx - x) - yaw
    alpha = math.atan2(math.sin(alpha), math.cos(alpha))
    set_cmd(speed, 2.0 * speed * math.sin(alpha) / lookahead)
    time.sleep(1 / freq)
