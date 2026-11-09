#!/usr/bin/env python3
"""Hangs the tomatoes and applies the harvest rules of the MMO-500 harvest head.

A tomato comes off when the three fingers hold it firmly and the head twists it.
Squeezing too hard bursts it and pulling before the twist tears its truss.

    harvest_manager.py greenhouse [seed]   random fruit all over the greenhouse
    harvest_manager.py bench               fixed fruit of the small practice world
"""

import argparse
import json
import math
import os
import random
import multiprocessing
import sys
import threading
import time
from dataclasses import dataclass, field
from enum import Enum

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy
from rclpy.utilities import remove_ros_args
from control_msgs.msg import JointTrajectoryControllerState
from sensor_msgs.msg import JointState
from std_msgs.msg import Float32, String

from gz.msgs10.boolean_pb2 import Boolean
from gz.msgs10.clock_pb2 import Clock as GzClock
from gz.msgs10.empty_pb2 import Empty
from gz.msgs10.entity_factory_pb2 import EntityFactory
from gz.msgs10.entity_factory_v_pb2 import EntityFactory_V
from gz.msgs10.entity_pb2 import Entity
from gz.msgs10.pose_v_pb2 import Pose_V
from gz.transport13 import Node as GzNode, SubscribeOptions

Vec3 = tuple[float, float, float]
Quat = tuple[float, float, float, float]
Pose6 = tuple[float, float, float, float, float, float]

WORLD = "default"
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
SCORE_TOPIC = "/tomato_greenhouse/score"
FORCE_TOPIC = "/tomato_greenhouse/grip_force"
STEP_PERIOD = 0.05
GZ_TIMEOUT = 6.0
SPAWN_TIMEOUT = 20.0

# Greenhouse trusses that get fruit, one per 2 m section of every plant line and the rest at random
TRUSS_COUNT = 60
ROW_START_X = -5.0
SECTION_LENGTH = 2.0
SECTIONS_PER_LINE = 5
MIN_FRUITS = 3
RIPE_TRUSSES_PER_LINE = 2

# Must match the harvest head of the MMO-500
ROBOT = "mmo500"
SPINDLE_LINK = "harvest_spindle"
TWIST_JOINT = "harvest_twist_joint"
GRIPPER_STATE_TOPIC = f"/{ROBOT}/gripper_controller/controller_state"
HOLD_OFFSET = 0.205
# A tomato is inside the finger cage when its center is this close to the grasp point, the splayed fingers center it
CAGE_RADIAL = 0.025
CAGE_AXIAL = 0.03
# Finger angle where the pads touch a centered tomato, smaller for a bigger one
CONTACT_AT_ZERO = 0.35
CONTACT_SLOPE = 8.33

# The soft pads squeeze harder the further the fingers are commanded past the contact
FORCE_GAIN = 40.0
GRIP_MIN = 1.0
CRUSH_RIPE = 2.5
CRUSH_GREEN = 5.0
TWIST_START = math.radians(10)
# Each stem snaps after its own number of turns somewhere in this range
SNAP_TURNS = (1.0, 2.0)
PULL_DISTANCE = 0.04

# Hanging tomatoes only collide near the head since hundreds of them slow the physics down
COLLIDER_ON = 0.30
COLLIDER_OFF = 0.40
# The fingers collide with 0x01 and loose fruit uses 0x02 so a held tomato never pushes the arm
FINGER_MASK = "0x01"
LOOSE_MASK = "0x02"
ALL_MASK = "0xffff"

# Crate carried by the robot, must match mmo500_harvest_gripper.urdf.xacro
CRATE_CENTER = (0.56, 0.0)
CRATE_HALF = (0.185, 0.285)
CRATE_FLOOR = 0.40
CRATE_HEIGHT = 0.14
# A falling tomato counts once it has been still for this long
SETTLE_TIME = 1.0
SETTLE_MOTION = 0.003
# Emitters are removed once their particles are gone
SPLASH_LIFE = 3.0

# Ripeness goes from 0 green to 1 deep red
COLOR_STOPS = [
    (0.00, (0.30, 0.55, 0.12)),
    (0.40, (0.55, 0.62, 0.14)),
    (0.60, (0.88, 0.52, 0.08)),
    (0.80, (0.86, 0.22, 0.05)),
    (1.00, (0.70, 0.05, 0.03)),
]
GREEN_LIMIT = 0.5
STALK_COLOR = "0.36 0.52 0.18 1"
FRUIT_DENSITY = 1000.0


class State(Enum):
    HANGING = "hanging"
    HELD = "held"
    IN_HAND = "in_hand"
    FALLING = "falling"
    CRUSHED = "crushed"
    SQUASHED = "squashed"
    HARVESTED = "harvested"
    LOST = "lost"


# SDF templates

FRUIT_COLLISION = """
      <collision name="collision">
        <geometry><ellipsoid><radii>{r:.4f} {r:.4f} {rz:.4f}</radii></ellipsoid></geometry>
        <surface>
          <friction><ode><mu>1.0</mu><mu2>1.0</mu2></ode></friction>
          <contact><collide_bitmask>{bitmask}</collide_bitmask></contact>
        </surface>
      </collision>"""

FRUIT_LINK = """
    <link name="fruit">
      <inertial>
        <mass>{mass:.4f}</mass>
        <inertia><ixx>{inertia:.3e}</ixx><iyy>{inertia:.3e}</iyy><izz>{inertia:.3e}</izz></inertia>
      </inertial>{collision}
      <visual name="visual">
        <geometry><ellipsoid><radii>{r:.4f} {r:.4f} {rz:.4f}</radii></ellipsoid></geometry>
        <material>
          <ambient>{cr:.3f} {cg:.3f} {cb:.3f} 1</ambient>
          <diffuse>{cr:.3f} {cg:.3f} {cb:.3f} 1</diffuse>
          <specular>0.5 0.5 0.5 1</specular>
        </material>
      </visual>
      <visual name="calyx">
        <pose>0 0 {calyx_z:.4f} 0 0 {calyx_yaw:.3f}</pose>
        <geometry><mesh><uri>model://tomato_fruit/meshes/calyx.obj</uri><scale>{cs:.4f} {cs:.4f} {cs:.4f}</scale></mesh></geometry>
        <material><ambient>0.22 0.40 0.10 1</ambient><diffuse>0.22 0.40 0.10 1</diffuse></material>
      </visual>{visuals}
    </link>"""

CRUSHED_LINK = """
    <link name="fruit">
      <inertial><mass>{mass:.4f}</mass><inertia><ixx>2e-5</ixx><iyy>2e-5</iyy><izz>2e-5</izz></inertia></inertial>
      <collision name="collision">
        <geometry><ellipsoid><radii>{rx:.4f} {ry:.4f} {rz:.4f}</radii></ellipsoid></geometry>
      </collision>
      <visual name="pulp">
        <geometry><ellipsoid><radii>{rx:.4f} {ry:.4f} {rz:.4f}</radii></ellipsoid></geometry>
        <material><ambient>{cr:.3f} {cg:.3f} {cb:.3f} 1</ambient><diffuse>{cr:.3f} {cg:.3f} {cb:.3f} 1</diffuse><specular>0.8 0.3 0.3 1</specular></material>
      </visual>
      <visual name="burst">
        <pose>{bx:.4f} {by:.4f} {bz:.4f} 0 0 0</pose>
        <geometry><sphere><radius>{br:.4f}</radius></sphere></geometry>
        <material><ambient>0.88 0.30 0.16 1</ambient><diffuse>0.88 0.30 0.16 1</diffuse><specular>1 0.6 0.6 1</specular></material>
      </visual>
    </link>"""

STALK_SEGMENT = """
      <visual name="{name}">
        <pose>{cx:.4f} {cy:.4f} {cz:.4f} 0 {pitch:.4f} {yaw:.4f}</pose>
        <geometry><cylinder><radius>{radius}</radius><length>{length:.4f}</length></cylinder></geometry>
        <material><ambient>{color}</ambient><diffuse>{color}</diffuse></material>
      </visual>"""

# Keeps a picked tomato in the hand until the fingers open
ATTACH_PLUGIN = """
    <plugin filename="gz-sim-detachable-joint-system" name="gz::sim::systems::DetachableJoint">
      <parent_link>fruit</parent_link>
      <child_model>{robot}</child_model>
      <child_link>{link}</child_link>
      <detach_topic>{topic}</detach_topic>
    </plugin>"""

# Short burst of particles, several of them in random directions make a splash
EMITTER = """
      <particle_emitter name="burst_{i}" type="point">
        <pose>0 0 0 0 {pitch:.3f} {yaw:.3f}</pose>
        <emitting>true</emitting>
        <duration>{duration}</duration>
        <particle_size>{size} {size} {size}</particle_size>
        <lifetime>{lifetime}</lifetime>
        <rate>{rate}</rate>
        <min_velocity>{vmin}</min_velocity>
        <max_velocity>{vmax}</max_velocity>
        <material><diffuse>{color} 1</diffuse><emissive>{glow} 1</emissive></material>
      </particle_emitter>"""
JUICE = dict(count=14, duration=0.15, size=0.004, lifetime=0.3, rate=120, vmin=0.05, vmax=0.35,
             color="0.8 0.06 0.03", glow="0.35 0.02 0.01")
STEM_BITS = dict(count=8, duration=0.25, size=0.0035, lifetime=1.3, rate=30, vmin=0.03, vmax=0.12,
                 color="0.42 0.62 0.20", glow="0.10 0.18 0.04")
TRUSS_BITS = dict(count=14, duration=0.3, size=0.004, lifetime=1.3, rate=40, vmin=0.04, vmax=0.18,
                  color="0.42 0.62 0.20", glow="0.10 0.18 0.04")


def sdf_model(name: str, pose: Pose6, body: str, static: bool) -> str:
    x, y, z, roll, pitch, yaw = pose
    return f"""<?xml version="1.0"?>
<sdf version="1.9">
  <model name="{name}">
    <static>{'true' if static else 'false'}</static>
    <pose>{x:.4f} {y:.4f} {z:.4f} {roll:.4f} {pitch:.4f} {yaw:.4f}</pose>{body}
  </model>
</sdf>
"""


def segment_visual(name: str, a: Vec3, b: Vec3, radius: float, origin: Vec3) -> str:
    dx, dy, dz = (b[i] - a[i] for i in range(3))
    cx, cy, cz = ((a[i] + b[i]) / 2 - origin[i] for i in range(3))
    return STALK_SEGMENT.format(
        name=name, cx=cx, cy=cy, cz=cz, pitch=math.atan2(math.hypot(dx, dy), dz), yaw=math.atan2(dy, dx),
        radius=radius, length=math.dist(a, b), color=STALK_COLOR)


def splash_sdf(name: str, pos: Vec3, kind: dict) -> str:
    params = {k: v for k, v in kind.items() if k != "count"}
    emitters = "".join(
        EMITTER.format(i=i, yaw=random.uniform(-math.pi, math.pi), pitch=random.uniform(-1.2, 1.2), **params)
        for i in range(kind["count"]))
    return sdf_model(name, (*pos, 0, 0, 0), f'\n    <link name="splash">{emitters}\n    </link>', True)


# Geometry

def rotate(q: Quat, v: Vec3) -> Vec3:
    x, y, z, w = q
    tx, ty, tz = 2 * (y * v[2] - z * v[1]), 2 * (z * v[0] - x * v[2]), 2 * (x * v[1] - y * v[0])
    return (v[0] + w * tx + y * tz - z * ty, v[1] + w * ty + z * tx - x * tz, v[2] + w * tz + x * ty - y * tx)


def quat_mul(a: Quat, b: Quat) -> Quat:
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)


def quat_to_rpy(x: float, y: float, z: float, w: float) -> Vec3:
    roll = math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    pitch = math.asin(max(-1.0, min(1.0, 2 * (w * y - z * x))))
    yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
    return roll, pitch, yaw


def grasp_point(spindle: tuple[Vec3, Quat]) -> tuple[Vec3, Vec3]:
    # The fingers close around a point along the spindle axis
    p, q = spindle
    axis = rotate(q, (0.0, 0.0, 1.0))
    return tuple(p[i] + axis[i] * HOLD_OFFSET for i in range(3)), axis


def ripeness_color(ripe: float) -> Vec3:
    for (r0, c0), (r1, c1) in zip(COLOR_STOPS, COLOR_STOPS[1:]):
        if ripe <= r1:
            t = (ripe - r0) / (r1 - r0)
            return tuple(a + (b - a) * t for a, b in zip(c0, c1))
    return COLOR_STOPS[-1][1]


# Tomatoes

@dataclass(eq=False)
class Tomato:
    name: str
    truss_id: int
    truss: dict
    j: int
    r: float
    rz: float
    ripe: float
    snap_turns: float = sum(SNAP_TURNS) / 2
    state: State = State.HANGING
    lost: bool = False
    # The tomato is respawned as it changes state so its gz entity name changes too
    entity: str = ""
    stalk_entity: str | None = None
    collider: str | None = None
    center: Vec3 = field(init=False)
    color: Vec3 = field(init=False)
    mass: float = field(init=False)
    calyx_yaw: float = field(init=False)

    def __post_init__(self):
        ax, ay, az = self.truss["anchors"][self.j]
        self.center = (ax, ay, az - self.rz - 0.002)
        self.color = ripeness_color(self.ripe)
        self.mass = FRUIT_DENSITY * 4.0 / 3.0 * math.pi * self.r * self.r * self.rz
        self.calyx_yaw = random.uniform(-math.pi, math.pi)
        self.entity = self.name

    @property
    def contact_angle(self) -> float:
        return CONTACT_AT_ZERO - CONTACT_SLOPE * self.r

    @property
    def crush_force(self) -> float:
        return CRUSH_RIPE + (CRUSH_GREEN - CRUSH_RIPE) * (1.0 - self.ripe)

    @property
    def hanging_pose(self) -> Pose6:
        return (*self.center, 0.0, 0.0, 0.0)

    @property
    def is_green(self) -> bool:
        return self.ripe < GREEN_LIMIT

    def hanging_sdf(self, name: str) -> str:
        link = self._fruit_link(self._stalk_visuals(pedicel=True), collision=None)
        return sdf_model(name, self.hanging_pose, link, True)

    def collider_sdf(self, name: str) -> str:
        # Invisible stand in that only the fingers bump into
        body = f'\n    <link name="fruit">{self._collision(FINGER_MASK)}\n    </link>'
        return sdf_model(name, self.hanging_pose, body, True)

    def stalk_sdf(self, name: str, pedicel: bool) -> str:
        body = f'\n    <link name="stalk">{self._stalk_visuals(pedicel)}\n    </link>'
        return sdf_model(name, self.hanging_pose, body, True)

    def loose_sdf(self, name: str, detach_topic: str | None = None) -> str:
        body = self._fruit_link(collision=LOOSE_MASK)
        if detach_topic:
            # The attach plugin belongs to the model so it goes after the link
            body += ATTACH_PLUGIN.format(robot=ROBOT, link=SPINDLE_LINK, topic=detach_topic)
        return sdf_model(name, self.hanging_pose, body, False)

    def rest_sdf(self, name: str, pose: Pose6) -> str:
        return sdf_model(name, pose, self._fruit_link(collision=ALL_MASK), True)

    def crushed_sdf(self, name: str, pose: Pose6, static: bool) -> str:
        cr, cg, cb = (c * 0.7 for c in self.color)
        r = self.r
        body = CRUSHED_LINK.format(
            mass=self.mass, rx=r * 1.2, ry=r * 1.1, rz=r * 0.45, cr=cr, cg=cg, cb=cb,
            bx=r * 0.3, by=-r * 0.25, bz=r * 0.3, br=r * 0.4)
        return sdf_model(name, pose, body, static)

    def _collision(self, bitmask: str) -> str:
        return FRUIT_COLLISION.format(r=self.r, rz=self.rz, bitmask=bitmask)

    def _fruit_link(self, visuals: str = "", collision: str | None = ALL_MASK) -> str:
        cr, cg, cb = self.color
        return FRUIT_LINK.format(
            mass=self.mass, inertia=0.4 * self.mass * self.r * self.r, r=self.r, rz=self.rz,
            cr=cr, cg=cg, cb=cb, calyx_z=self.rz * 0.97, cs=self.r * 0.55, calyx_yaw=self.calyx_yaw,
            collision=self._collision(collision) if collision else "", visuals=visuals)

    def _stalk_visuals(self, pedicel: bool) -> str:
        # Piece of truss this tomato hangs from, the first one also carries the peduncle
        stalk = self.truss["stalk"]
        first = 0 if self.j == 0 else 2 + self.j
        visuals = [segment_visual(f"stalk_{i}", stalk[i], stalk[i + 1], 0.004, self.center)
                   for i in range(first, 3 + self.j)]
        if pedicel:
            a, b = self.truss["pedicels"][self.j]
            visuals.append(segment_visual("pedicel", a, b, 0.002, self.center))
        return "".join(visuals)


Fruit = tuple[dict[str, Tomato], dict[int, list[Tomato]]]


def bench_fruit(bench: dict) -> Fruit:
    tomatoes, trusses = {}, {}
    for truss_id, truss in enumerate(bench["trusses"]):
        trusses[truss_id] = []
        for j, (r, ripe, turns) in enumerate(truss["fruit"]):
            t = Tomato(f"tomato_{len(tomatoes)}", truss_id, truss, j, r, r * 0.85, ripe, turns)
            tomatoes[t.name] = t
            trusses[truss_id].append(t)
    return tomatoes, trusses


def greenhouse_sections(trusses: list[dict]) -> dict[tuple[int, int], list[dict]]:
    sections = {}
    for truss in trusses:
        x = truss["anchors"][0][0]
        section = min(SECTIONS_PER_LINE - 1, max(0, int((x - ROW_START_X) / SECTION_LENGTH)))
        sections.setdefault((truss["line"], section), []).append(truss)
    return sections


def greenhouse_fruit(sections: dict[tuple[int, int], list[dict]]) -> Fruit:
    keys = list(sections)
    per_section = {k: TRUSS_COUNT // len(keys) for k in keys}
    for k in random.sample(keys, TRUSS_COUNT % len(keys)):
        per_section[k] += 1
    picked = []
    for k, n in per_section.items():
        picked += random.sample(sections[k], min(n, len(sections[k])))

    # Lower trusses are older and riper and every line gets some ripe ones
    bases = [1.0 - 0.12 * t["level"] + random.gauss(0.0, 0.25) for t in picked]
    by_line = {}
    for i, truss in enumerate(picked):
        by_line.setdefault(truss["line"], []).append(i)
    for indices in by_line.values():
        for i in random.sample(indices, min(RIPE_TRUSSES_PER_LINE, len(indices))):
            bases[i] = max(bases[i], random.uniform(0.95, 1.1))

    tomatoes, trusses = {}, {}
    for truss_id, (truss, base) in enumerate(zip(picked, bases)):
        # Fruit fills a truss from the stem outwards and ripens in the same order
        count = random.randint(MIN_FRUITS, len(truss["anchors"]))
        radius = random.uniform(0.024, 0.036)
        trusses[truss_id] = []
        for j in range(count):
            ripe = min(1.0, max(0.0, base - 0.03 * j + random.gauss(0.0, 0.05)))
            r = radius * (1.0 - 0.04 * j) * random.uniform(0.92, 1.05)
            t = Tomato(f"tomato_{len(tomatoes)}", truss_id, truss, j, r, r * random.uniform(0.80, 0.90), ripe,
                       random.uniform(*SNAP_TURNS))
            tomatoes[t.name] = t
            trusses[truss_id].append(t)
    return tomatoes, trusses


def read_data(name: str) -> dict:
    with open(os.path.join(DATA_DIR, name)) as fh:
        return json.load(fh)


# gz

def gz_service_worker(conn):
    """Serves the gz requests of the manager from a process without gz subscriptions."""
    node = GzNode()
    while True:
        job = conn.recv()
        if job is None:
            return
        job_id, service, data, timeout = job
        if service == "remove":
            request, req_type = Entity(name=data, type=Entity.MODEL), Entity
        else:
            factories = [EntityFactory(sdf=sdf, name=name, allow_renaming=False) for name, sdf in data]
            if service == "create":
                request, req_type = factories[0], EntityFactory
            else:
                request, req_type = EntityFactory_V(data=factories), EntityFactory_V
        try:
            ok, reply = node.request(f"/world/{WORLD}/{service}", request, req_type, Boolean, int(timeout * 1000))
            conn.send((job_id, bool(ok and reply.data)))
        except Exception:
            conn.send((job_id, False))


class GzWorld:
    """Spawns and removes models of the running world.

    Blocking gz requests deadlock with the gz subscriptions of the same Python
    process, so they are served by a helper process that has none.
    """

    def __init__(self, logger):
        self._logger = logger
        self._counter = 0
        self._job = 0
        self._lock = threading.Lock()
        context = multiprocessing.get_context("spawn")
        self._conn, child = context.Pipe()
        self._worker = context.Process(target=gz_service_worker, args=(child,), daemon=True)
        self._worker.start()

    def unique(self, base: str) -> str:
        self._counter += 1
        return f"{base}_{self._counter}"

    def create(self, name: str, sdf: str) -> bool:
        return self.create_many([(name, sdf)])

    def create_many(self, models: list[tuple[str, str]], timeout: float = GZ_TIMEOUT) -> bool:
        service = "create" if len(models) == 1 else "create_multiple"
        ok = self._call(service, models, timeout)
        if not ok:
            self._logger.error(f"failed to spawn {', '.join(name for name, _ in models)}")
        return ok

    def remove(self, name: str) -> bool:
        return self._call("remove", name, GZ_TIMEOUT)

    def close(self):
        with self._lock:
            try:
                self._conn.send(None)
            except (EOFError, OSError):
                pass
        self._worker.join(timeout=2.0)

    def _call(self, service: str, data, timeout: float) -> bool:
        with self._lock:
            self._job += 1
            job = self._job
            try:
                self._conn.send((job, service, data, timeout))
                # A reply that arrives after its timeout belongs to an older job and is skipped
                deadline = time.monotonic() + timeout + 1.0
                while self._conn.poll(max(0.0, deadline - time.monotonic())):
                    reply_job, ok = self._conn.recv()
                    if reply_job == job:
                        return ok
            except (EOFError, OSError):
                self._logger.error("the gz helper process is gone")
            return False


# Manager

@dataclass
class Grip:
    """Tomato between the fingers and where the grip started."""

    tomato: Tomato
    tcp: Vec3
    twist: float


def new_score() -> dict[str, int]:
    return {"harvested": 0, "green_in_crate": 0, "crushed": 0, "dropped": 0, "broken_trusses": 0}


class HarvestManager(Node):
    def __init__(self, layout: str):
        super().__init__("harvest_manager")

        if layout == "bench":
            bench = read_data("bench_layout.json")
            self._make_fruit = lambda: bench_fruit(bench)
        else:
            sections = greenhouse_sections(read_data("tomato_anchors.json")["trusses"])
            self._make_fruit = lambda: greenhouse_fruit(sections)

        self._gz = GzWorld(self.get_logger())
        self._tomatoes: dict[str, Tomato] = {}
        self._trusses: dict[int, list[Tomato]] = {}
        self._grip: Grip | None = None
        # Tomato inside the cage while the fingers were still open, only it can be gripped
        self._open_around: Tomato | None = None
        self._settling: dict[str, tuple[float, Vec3]] = {}
        self._splashes: list[tuple[float, str]] = []
        self._detach_pubs = {}
        self._score = new_score()

        # Latest robot state from the topics
        self._finger_ref = 0.0
        self._twist = 0.0
        self._spindle: tuple[Vec3, Quat] | None = None
        self._poses: dict[str, tuple[Vec3, Quat]] = {}
        self._last_sim_time = 0.0

        self._lock = threading.Lock()
        # Restarts and rule steps change the world one at a time
        self._ops = threading.Lock()
        self._stop = threading.Event()

        self.create_subscription(JointState, f"/{ROBOT}/joint_states", self._on_joints, 10)
        self.create_subscription(JointTrajectoryControllerState, GRIPPER_STATE_TOPIC, self._on_gripper, 10)
        # Latched so the HAL gets the current score when it starts
        latched = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self._score_pub = self.create_publisher(String, SCORE_TOPIC, latched)
        self._force_pub = self.create_publisher(Float32, FORCE_TOPIC, 10)

        self._gz_node = GzNode()
        self._gz_topics: list[str] = []
        self._gz_subscribe(Pose_V, f"/world/{WORLD}/dynamic_pose/info", self._on_poses, 20)
        # The ROS clock arrives every physics step and only resets matter here
        self._gz_subscribe(GzClock, f"/world/{WORLD}/clock", self._on_clock, 10)

        # The rules wait for gz calls so they run apart from the ROS callbacks
        self._rules_thread = threading.Thread(target=self._rules_loop, daemon=True)
        self._rules_thread.start()
        threading.Thread(target=self._restart, daemon=True).start()

        self.get_logger().info(f"harvest_manager ready with the {layout} layout")

    def destroy_node(self):
        self._stop.set()
        self._rules_thread.join(timeout=2 * GZ_TIMEOUT)
        for topic in self._gz_topics:
            self._gz_node.unsubscribe(topic)
        self._gz.close()
        super().destroy_node()

    # Inputs

    def _gz_subscribe(self, msg_type, topic: str, callback, rate: int):
        options = SubscribeOptions()
        options.msgs_per_sec = rate
        self._gz_node.subscribe(msg_type, topic, callback, options)
        self._gz_topics.append(topic)

    def _on_clock(self, msg: GzClock):
        # Sim time going backwards means the world was reset
        t = msg.sim.sec + msg.sim.nsec * 1e-9
        if t < self._last_sim_time:
            threading.Thread(target=self._restart, daemon=True).start()
        self._last_sim_time = t

    def _on_joints(self, msg: JointState):
        if TWIST_JOINT in msg.name:
            self._twist = msg.position[msg.name.index(TWIST_JOINT)]

    def _on_gripper(self, msg: JointTrajectoryControllerState):
        if msg.reference.positions:
            self._finger_ref = msg.reference.positions[0]

    def _on_poses(self, msg: Pose_V):
        poses = {}
        for pose in msg.pose:
            p, q = pose.position, pose.orientation
            poses[pose.name] = ((p.x, p.y, p.z), (q.x, q.y, q.z, q.w))
        with self._lock:
            self._poses.update(poses)
            # Links come relative to their model so the spindle is composed with the robot pose
            if ROBOT in poses and SPINDLE_LINK in poses:
                (mp, mq), (lp, lq) = poses[ROBOT], poses[SPINDLE_LINK]
                r = rotate(mq, lp)
                self._spindle = ((mp[0] + r[0], mp[1] + r[1], mp[2] + r[2]), quat_mul(mq, lq))

    def _pose_of(self, entity: str) -> tuple[Vec3, Quat] | None:
        with self._lock:
            return self._poses.get(entity)

    # Main loop

    def _restart(self):
        # A world reset already removes everything spawned at runtime
        with self._ops:
            tomatoes, trusses = self._make_fruit()
            self._gz.create_many([(t.name, t.hanging_sdf(t.name)) for t in tomatoes.values()], SPAWN_TIMEOUT)
            self._tomatoes, self._trusses = tomatoes, trusses
            self._grip = None
            self._open_around = None
            self._settling, self._splashes, self._detach_pubs = {}, [], {}
            self._score = new_score()
            self._publish_score()
            self.get_logger().info(f"{len(tomatoes)} tomatoes hanging")

    def _rules_loop(self):
        # Stops as soon as ROS shuts down so nothing is published on a dead context
        while not self._stop.wait(STEP_PERIOD) and rclpy.ok():
            # A restart in progress owns the world so this step is skipped
            if not self._ops.acquire(blocking=False):
                continue
            try:
                self._step()
            except Exception as error:
                self.get_logger().error(f"harvest rules failed: {error!r}")
            finally:
                self._ops.release()

    def _step(self):
        with self._lock:
            spindle = self._spindle
        force = 0.0
        if spindle:
            tcp, axis = grasp_point(spindle)
            # Colliders first so they are in place before the fingers arrive
            self._update_colliders(tcp)
            force = self._update_grip(tcp, axis)
        self._force_pub.publish(Float32(data=float(force)))
        self._update_falling()
        self._clear_splashes()

    # Colliders

    def _update_colliders(self, tcp: Vec3):
        new = []
        for t in self._tomatoes.values():
            distance = math.dist(t.center, tcp)
            if t.collider and (t.state is not State.HANGING or distance > COLLIDER_OFF):
                self._remove_collider(t)
            elif not t.collider and t.state is State.HANGING and distance < COLLIDER_ON \
                    and self._finger_ref < t.contact_angle:
                # Fingers already closed past the fruit would get stuck inside a new collider
                t.collider = self._gz.unique(f"{t.name}_col")
                new.append((t.collider, t.collider_sdf(t.collider)))
        if new:
            self._gz.create_many(new)

    def _remove_collider(self, t: Tomato):
        if t.collider:
            self._gz.remove(t.collider)
            t.collider = None

    # Grip rules

    def _update_grip(self, tcp: Vec3, axis: Vec3) -> float:
        if self._grip is None:
            t = self._tomato_in_cage(tcp, axis)
            if t is None:
                self._open_around = None
                return 0.0
            if self._finger_ref < t.contact_angle:
                self._open_around = t
                return 0.0
            if self._open_around is not t:
                # Fingers that closed somewhere else only bump into the fruit
                return 0.0
            self._grip = Grip(t, tcp, self._twist)
            # A static collider would hold the fingers like a post and drag the robot when it pulls or twists
            self._remove_collider(t)

        grip = self._grip
        t = grip.tomato
        touching = self._finger_ref >= t.contact_angle
        force = FORCE_GAIN * (self._finger_ref - t.contact_angle) if touching else 0.0
        firm = force >= GRIP_MIN
        twisted = abs(self._twist - grip.twist)
        moved = math.dist(tcp, grip.tcp) > PULL_DISTANCE

        if force > t.crush_force:
            self._burst(t)
            self._grip = None
        elif t.state is State.HANGING:
            if not touching:
                self._grip = None
            elif moved:
                if firm:
                    self._tear_truss(t)
                self._grip = None
            elif twisted > TWIST_START:
                if firm:
                    self._start_hold(t)
                else:
                    # A loose grip slips around the fruit without turning it
                    grip.twist = self._twist
        elif t.state is State.HELD:
            if not firm:
                self._put_back(t)
                self._grip = None
            elif twisted >= t.snap_turns * 2 * math.pi:
                self._snap(t)
            elif moved:
                self._tear_truss(t)
                self._grip = None
        elif t.state is State.IN_HAND and not touching:
            known = self._pose_of(t.entity)
            where = self._robot_frame(known[0]) if known else None
            at = f" at ({where[0]:.2f}, {where[1]:.2f}, {where[2]:.2f}) in the robot frame" if where else ""
            self.get_logger().info(f"{t.name} released{at}")
            self._drop(t, lost=False)
            self._grip = None
        return force

    def _tomato_in_cage(self, tcp: Vec3, axis: Vec3) -> Tomato | None:
        for t in self._tomatoes.values():
            if t.state is not State.HANGING:
                continue
            d = [t.center[i] - tcp[i] for i in range(3)]
            along = sum(d[i] * axis[i] for i in range(3))
            radial = math.sqrt(max(0.0, sum(v * v for v in d) - along * along))
            if radial < CAGE_RADIAL and abs(along) < CAGE_AXIAL:
                return t
        return None

    # Tomato transitions

    def _start_hold(self, t: Tomato):
        # From now on the fruit turns with the fingers while its stalk stays on the plant
        self.get_logger().info(f"{t.name} held")
        self._remove_collider(t)
        self._gz.remove(t.entity)
        self._respawn_stalk(t, pedicel=True)
        t.entity = self._gz.unique(t.name)
        topic = f"/tomato_greenhouse/{t.entity}/detach"
        self._detach_pubs[t.entity] = self._gz_node.advertise(topic, Empty)
        self._gz.create(t.entity, t.loose_sdf(t.entity, topic))
        t.state = State.HELD

    def _snap(self, t: Tomato):
        self.get_logger().info(f"{t.name} picked")
        self._respawn_stalk(t, pedicel=False)
        t.state = State.IN_HAND

    def _put_back(self, t: Tomato):
        # Released before the stem snapped so the tomato stays on the plant
        self.get_logger().info(f"{t.name} slipped back onto the plant")
        self._detach_pubs.pop(t.entity, None)
        self._gz.remove(t.entity)
        self._remove_stalk(t)
        t.entity = self._gz.unique(t.name)
        self._gz.create(t.entity, t.hanging_sdf(t.entity))
        t.state = State.HANGING

    def _burst(self, t: Tomato):
        self.get_logger().info(f"{t.name} burst")
        pose = t.hanging_pose
        known = self._pose_of(t.entity) if t.state in (State.HELD, State.IN_HAND) else None
        if known:
            pose = (*known[0], *quat_to_rpy(*known[1]))
        self._detach_pubs.pop(t.entity, None)
        self._remove_collider(t)
        self._gz.remove(t.entity)
        t.entity = self._gz.unique(f"{t.name}_crushed")
        self._gz.create(t.entity, t.crushed_sdf(t.entity, pose, static=False))
        self._splash(f"{t.name}_juice", pose[:3], JUICE)
        t.state = State.CRUSHED
        self._count("crushed")

    def _tear_truss(self, t: Tomato):
        self.get_logger().info(f"truss of {t.name} torn")
        stalk = t.truss["stalk"]
        self._splash(f"{t.name}_truss", stalk[0], TRUSS_BITS)
        self._splash(f"{t.name}_rachis", stalk[len(stalk) // 2 + 1], STEM_BITS)
        self._remove_stalk(t)
        for other in self._trusses[t.truss_id]:
            if other.state in (State.HANGING, State.HELD):
                self._drop(other, lost=True)
        self._count("broken_trusses")

    def _drop(self, t: Tomato, lost: bool):
        # A held tomato is already loose and only needs its joint released
        if t.entity in self._detach_pubs:
            self._detach_pubs.pop(t.entity).publish(Empty())
        else:
            self._gz.remove(t.entity)
            t.entity = self._gz.unique(t.name)
            self._gz.create(t.entity, t.loose_sdf(t.entity))
        # A lost tomato never counts as harvested even if it lands in a crate
        t.lost = lost
        t.state = State.FALLING

    def _respawn_stalk(self, t: Tomato, pedicel: bool):
        self._remove_stalk(t)
        t.stalk_entity = self._gz.unique(f"{t.name}_stalk")
        self._gz.create(t.stalk_entity, t.stalk_sdf(t.stalk_entity, pedicel))

    def _remove_stalk(self, t: Tomato):
        if t.stalk_entity:
            self._gz.remove(t.stalk_entity)
            t.stalk_entity = None

    # Landing

    def _update_falling(self):
        now = time.monotonic()
        for t in self._tomatoes.values():
            if t.state not in (State.FALLING, State.CRUSHED):
                continue
            known = self._pose_of(t.entity)
            if known is None:
                continue
            pos, quat = known
            if self._in_crate(pos):
                self._collect(t)
                continue
            start = self._settling.get(t.name)
            if start is None or math.dist(pos, start[1]) > SETTLE_MOTION:
                self._settling[t.name] = (now, pos)
            elif now - start[0] >= SETTLE_TIME:
                del self._settling[t.name]
                self._land(t, (*pos, *quat_to_rpy(*quat)))

    def _land(self, t: Tomato, pose: Pose6):
        # Still for long enough so it becomes static and stops costing physics
        self._gz.remove(t.entity)
        rest = self._gz.unique(f"{t.name}_rest")
        if t.state is State.CRUSHED:
            self._gz.create(rest, t.crushed_sdf(rest, pose, static=True))
            t.state = State.SQUASHED
        else:
            self._gz.create(rest, t.rest_sdf(rest, pose))
            t.state = State.LOST
            self._count("dropped")
        t.entity = rest

    def _collect(self, t: Tomato):
        # Fruit inside the crate is counted and removed so it costs nothing while the robot drives on
        self._settling.pop(t.name, None)
        self._gz.remove(t.entity)
        if t.state is State.CRUSHED:
            t.state = State.SQUASHED
        elif t.lost:
            t.state = State.LOST
            self._count("dropped")
        else:
            self.get_logger().info(f"{t.name} harvested")
            t.state = State.HARVESTED
            self._count("harvested")
            if t.is_green:
                self._count("green_in_crate")

    def _robot_frame(self, pos: Vec3) -> Vec3 | None:
        robot = self._pose_of(ROBOT)
        if robot is None:
            return None
        (rx, ry, rz), (qx, qy, qz, qw) = robot
        return rotate((-qx, -qy, -qz, qw), (pos[0] - rx, pos[1] - ry, pos[2] - rz))

    def _in_crate(self, pos: Vec3) -> bool:
        local = self._robot_frame(pos)
        if local is None:
            return False
        x, y, z = local
        return (abs(x - CRATE_CENTER[0]) < CRATE_HALF[0] and abs(y - CRATE_CENTER[1]) < CRATE_HALF[1]
                and CRATE_FLOOR - 0.02 < z < CRATE_FLOOR + CRATE_HEIGHT)

    # Effects and score

    def _splash(self, base: str, pos: Vec3, kind: dict):
        name = self._gz.unique(base)
        self._gz.create(name, splash_sdf(name, pos, kind))
        self._splashes.append((time.monotonic() + SPLASH_LIFE, name))

    def _clear_splashes(self):
        while self._splashes and self._splashes[0][0] < time.monotonic():
            self._gz.remove(self._splashes.pop(0)[1])

    def _count(self, key: str):
        self._score[key] += 1
        self._publish_score()

    def _publish_score(self):
        self._score_pub.publish(String(data=json.dumps(self._score)))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tomato harvest rules for the MMO-500")
    parser.add_argument("layout", nargs="?", default="greenhouse", choices=["greenhouse", "bench"])
    parser.add_argument("seed", nargs="?", type=int, help="fixes the random fruit of the greenhouse")
    return parser.parse_args(remove_ros_args(argv)[1:])


def main():
    args = parse_args(sys.argv)
    if args.seed is not None:
        random.seed(args.seed)
    rclpy.init()
    node = HarvestManager(args.layout)
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
