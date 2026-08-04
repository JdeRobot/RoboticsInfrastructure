import time
import math
import rclpy
import threading
import time
import sys

sys.path.insert(0, "/workspace/code")

from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, qos_profile_sensor_data

from hal_interfaces.general.camera import CameraNode
from jderobot_drones.drone_wrapper import DroneWrapper

IMG_WIDTH = 320
IMG_HEIGHT = 240
freq = 30.0

DRONE_NAMESPACE = "drone_mouse"
CAT_NAMESPACE = "drone"

DEFAULT_COURSE = "medium"
COURSE_TIMEOUT = 10.0


### HAL INIT ###

if not rclpy.ok():
    rclpy.init()


CAM_FRONTAL_TOPIC = "/" + DRONE_NAMESPACE + "/frontal_cam/image_raw"
CAM_VENTRAL_TOPIC = "/" + DRONE_NAMESPACE + "/ventral_cam/image_raw"
CAT_POSE_TOPIC = "/" + CAT_NAMESPACE + "/self_localization/pose"
COURSE_TOPIC = "/drone_cat_mouse/course"

drone = DroneWrapper(DRONE_NAMESPACE)
frontal_camera_node = CameraNode(CAM_FRONTAL_TOPIC)
ventral_camera_node = CameraNode(CAM_VENTRAL_TOPIC)

# Spin nodes so that subscription callbacks load topic data
executor = rclpy.executors.MultiThreadedExecutor()
executor.add_node(frontal_camera_node)
executor.add_node(ventral_camera_node)

cat_position = [0.0, 0.0, 0.0]
course = None


def cat_pose_callback(msg):
    cat_position[0] = msg.pose.position.x
    cat_position[1] = msg.pose.position.y
    cat_position[2] = msg.pose.position.z


def course_callback(msg):
    global course
    course = msg.data


cat_pose_node = rclpy.create_node("cat_pose_node")
cat_pose_node.create_subscription(
    PoseStamped, CAT_POSE_TOPIC, cat_pose_callback, qos_profile_sensor_data
)
# Latched by the world launcher, so it arrives however late this starts
cat_pose_node.create_subscription(
    String,
    COURSE_TOPIC,
    course_callback,
    QoSProfile(depth=1, durability=QoSDurabilityPolicy.TRANSIENT_LOCAL),
)
executor.add_node(cat_pose_node)


def __auto_spin() -> None:
    while rclpy.ok():
        try:
            executor.spin_once(timeout_sec=0)
        except Exception:
            pass
        time.sleep(1 / freq)


executor_thread = threading.Thread(target=__auto_spin, daemon=True)
executor_thread.start()

### GETTERS ###


def get_frontal_image():
    image = frontal_camera_node.getImage()
    while image is None:
        image = frontal_camera_node.getImage()
    return image.data


def get_ventral_image():
    image = ventral_camera_node.getImage()
    while image is None:
        image = ventral_camera_node.getImage()
    return image.data


def get_position():
    pos = drone.get_position()
    return pos


def get_velocity():
    vel = drone.get_velocity()
    return vel


def get_yaw_rate():
    yaw_rate = drone.get_yaw_rate()
    return yaw_rate


def get_orientation():
    orientation = drone.get_orientation()
    return orientation


def get_roll():
    roll = drone.get_roll()
    return roll


def get_pitch():
    pitch = drone.get_pitch()
    return pitch


def get_yaw():
    yaw = drone.get_yaw()
    return yaw


def get_landed_state():
    state = drone.get_landed_state()
    return state


def get_cat_position():
    return list(cat_position)


def get_course():
    give_up_at = time.time() + COURSE_TIMEOUT
    while course is None and time.time() < give_up_at:
        time.sleep(0.05)
    return course or DEFAULT_COURSE


### SETTERS ###


def set_cmd_pos(x, y, z, az):
    drone.set_cmd_pos(x, y, z, az)


def set_cmd_vel(vx, vy, vz, az):
    drone.set_cmd_vel(vx, vy, vz, az)


def set_cmd_mix(vx, vy, z, az):
    drone.set_cmd_mix(vx, vy, z, az)


def takeoff(h=3):
    drone.takeoff(h)


def land():
    drone.land()


COURSES = {
    "easy": {
        "V_MAX": 1.8,
        "V_MIN": 1.0,
        "THREAT_RADIUS": 0.0,
        "DODGE_GAIN": 0.0,
        "JUKE_FLIP": 99.0,
        "GATES": [
            (-15.5, 5.0, 4.0),
            (32.0, 5.0, 4.0),
        ],
    },
    "medium": {
        "V_MAX": 2.2,
        "V_MIN": 1.0,
        "THREAT_RADIUS": 6.0,
        "DODGE_GAIN": 1.8,
        "JUKE_FLIP": 2.0,
        "GATES": [
            (28.0, 3.0, 4.0),
            (28.0, -18.0, 4.0),
            (8.0, -18.0, 4.0),
            (8.0, 3.0, 4.0),
        ],
    },
    "hard": {
        "V_MAX": 2.2,
        "V_MIN": 1.0,
        "THREAT_RADIUS": 6.0,
        "DODGE_GAIN": 2.2,
        "JUKE_FLIP": 1.6,
        "GATES": [
            (-12.0, 4.0, 5.6),
            (20.7, 1.5, 3.0),
            (25.5, 4.3, 3.0),
            (30.3, 1.5, 3.2),
            (30.3, -3.9, 3.0),
            (25.5, -6.7, 3.0),
            (0.0, -16.0, 5.8),
            (4.0, -10.0, 3.4),
            (3.0, -2.0, 5.6),
            (0.0, 4.0, 4.0),
        ],
    },
}

TIME_LIMIT = {
    "easy": 30.0,
    "medium": 60.0,
    "hard": 90.0,
}

course_name = get_course()
course = COURSES.get(course_name, COURSES["medium"])
LIMIT = TIME_LIMIT[course_name]
print(
    "mouse flying the %s course, %.0f seconds on the clock" % (course_name, LIMIT),
    flush=True,
)

CRUISE_SPEED = course["V_MAX"]
CORNER_SPEED = course["V_MIN"]
CORNER_BRAKE = 1.4
ACCEL_MAX = 3.5
BRAKE_DISTANCE = 9.0
GATE_RADIUS = 4.5
YAW_GAIN = 2.0

THREAT_RADIUS = course["THREAT_RADIUS"]
DODGE_GAIN = course["DODGE_GAIN"]
JUKE_FLIP = course["JUKE_FLIP"]

TAKEOFF_HEIGHT = 4.0
CATCH_RADIUS = 1.8

HEAD_ON = 0.35
CLIMB_AWAY = 1.6
CEILING = 8.5

GATES = course["GATES"]


def clamp(value, low, high):
    return max(low, min(high, value))


def wrap(angle):
    return (angle + math.pi) % (2 * math.pi) - math.pi


def dist_xy(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def dist3(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def score_for(seconds):
    left = 1.0 - seconds / LIMIT
    return max(10, int(round(100 * left)))


takeoff(TAKEOFF_HEIGHT)

gate_index = 0
speed_x = speed_y = speed_z = 0.0
started = time.time()
juke_side = 1.0
last_flip = 0.0

recover_height = TAKEOFF_HEIGHT
checkpoint = get_position()
last_progress = time.time()
recovering = False
current_speed = 0.0
caught = False
landed = False
closest = 1e9

while True:
    elapsed = time.time() - started
    position = get_position()
    cat = get_cat_position()
    now = time.time()

    cat_known = any(abs(c) > 1e-6 for c in cat)
    airborne = position[2] > 1.0

    if cat_known and airborne:
        closest = min(closest, dist3(position, cat))

    if not caught and cat_known and airborne and dist3(position, cat) < CATCH_RADIUS:
        caught = True
        print("", flush=True)
        print("CAUGHT after %.1f of %.0f seconds" % (elapsed, LIMIT), flush=True)
        print("SCORE %d out of 100" % score_for(elapsed), flush=True)
        print("", flush=True)

    if not caught and elapsed > LIMIT:
        caught = True
        print("", flush=True)
        print(
            "ESCAPED, the %s mouse survived %.0f seconds" % (course_name, LIMIT),
            flush=True,
        )
        print(
            "closest the cat ever got was %.1f m, it needed %.1f"
            % (closest, CATCH_RADIUS),
            flush=True,
        )
        print("SCORE 0 out of 100", flush=True)
        print("", flush=True)

    if caught:
        if not landed:
            land()
            landed = True
        time.sleep(0.05)
        continue

    moving = current_speed > 0.5
    if dist3(position, checkpoint) > 0.4 or not moving:
        checkpoint = position
        last_progress = now
    stuck = (now - last_progress > 2.5) or (position[2] < TAKEOFF_HEIGHT * 0.4)
    if stuck and not recovering:
        recovering = True
        recover_height = min(TAKEOFF_HEIGHT, recover_height + 0.5)
    if recovering:
        set_cmd_vel(0.0, 0.0, 1.5, 0.0)
        if position[2] >= recover_height - 0.2:
            recovering = False
            checkpoint = position
            last_progress = now
        speed_x = speed_y = speed_z = 0.0
        current_speed = 0.0
        time.sleep(0.05)
        continue

    gate = GATES[gate_index]
    previous_gate = GATES[gate_index - 1]
    leg_in = (gate[0] - previous_gate[0], gate[1] - previous_gate[1])
    to_gate = (gate[0] - position[0], gate[1] - position[1])
    behind = (to_gate[0] * leg_in[0] + to_gate[1] * leg_in[1]) < 0

    if dist_xy(position, gate) < GATE_RADIUS or behind:
        gate_index = (gate_index + 1) % len(GATES)
        gate = GATES[gate_index]

    next_gate = GATES[(gate_index + 1) % len(GATES)]

    offset = (gate[0] - position[0], gate[1] - position[1], gate[2] - position[2])
    distance = math.sqrt(offset[0] ** 2 + offset[1] ** 2 + offset[2] ** 2) + 1e-6
    heading = (offset[0] / distance, offset[1] / distance, offset[2] / distance)

    leg_out = (next_gate[0] - gate[0], next_gate[1] - gate[1])
    leg_length = math.hypot(leg_out[0], leg_out[1]) + 1e-6
    alignment = (heading[0] * leg_out[0] + heading[1] * leg_out[1]) / leg_length
    turn_angle = math.acos(clamp(alignment, -1.0, 1.0))
    corner_ease = 1.0 / (1.0 + CORNER_BRAKE * turn_angle)
    nearness = clamp(
        (BRAKE_DISTANCE - dist_xy(position, gate)) / BRAKE_DISTANCE, 0.0, 1.0
    )
    speed = max(CORNER_SPEED, CRUISE_SPEED * (1.0 - nearness * (1.0 - corner_ease)))

    want_x = heading[0] * speed
    want_y = heading[1] * speed
    want_z = heading[2] * speed

    cat_ahead = 0.0
    cat_range = 1e9
    if cat_known:
        to_cat = (cat[0] - position[0], cat[1] - position[1])
        cat_range = math.hypot(to_cat[0], to_cat[1]) + 1e-6
        cat_ahead = (heading[0] * to_cat[0] + heading[1] * to_cat[1]) / cat_range

    if cat_known and cat_range < THREAT_RADIUS * 1.6 and cat_ahead > HEAD_ON:
        room = clamp(CEILING - position[2], 0.0, 1.0)
        urgency = clamp((THREAT_RADIUS * 1.6 - cat_range) / THREAT_RADIUS, 0.0, 1.0)
        want_z += CLIMB_AWAY * urgency * room

    cat_distance = dist_xy(position, cat)
    if cat_distance < THREAT_RADIUS:
        push = (THREAT_RADIUS - cat_distance) / THREAT_RADIUS
        away_x = (position[0] - cat[0]) / (cat_distance + 1e-6)
        away_y = (position[1] - cat[1]) / (cat_distance + 1e-6)
        if elapsed - last_flip > JUKE_FLIP:
            juke_side *= -1.0
            last_flip = elapsed
        side_x, side_y = -away_y * juke_side, away_x * juke_side
        want_x = (1 - push) * want_x + push * (side_x + 0.4 * away_x) * DODGE_GAIN
        want_y = (1 - push) * want_y + push * (side_y + 0.4 * away_y) * DODGE_GAIN

    max_step = ACCEL_MAX * 0.05
    speed_x += clamp(want_x - speed_x, -max_step, max_step)
    speed_y += clamp(want_y - speed_y, -max_step, max_step)
    speed_z += clamp(want_z - speed_z, -max_step, max_step)

    yaw = 0.0
    if math.hypot(speed_x, speed_y) > 0.3:
        yaw = YAW_GAIN * wrap(math.atan2(speed_y, speed_x) - get_yaw())

    current_speed = math.sqrt(speed_x**2 + speed_y**2 + speed_z**2)
    set_cmd_vel(speed_x, speed_y, speed_z, yaw)
    time.sleep(0.05)
