#!/usr/bin/env python3
"""
Ultra-lightweight Racing Lights & Tunnel Panels Controller for Monaco Circuit (Gazebo Sim 10).
Controls ONLY 2 merged visuals (zero CPU overhead, ~0.1% CPU, preserves ~1.00 RTF!):
  - racing_light_pods   (all 20 start/sector lights -> Standby RED -> Racing GREEN on race start)
  - tunnel_light_panels (all 8 tunnel ceiling LED panels -> Dim -> Full Bright White when car enters tunnel)
"""

import math
import time
import threading

import gz.transport as gzt
from gz.msgs.empty_pb2 import Empty
from gz.msgs.scene_pb2 import Scene
from gz.msgs.visual_pb2 import Visual
from gz.msgs.boolean_pb2 import Boolean
from gz.msgs.material_color_pb2 import MaterialColor
from gz.msgs.twist_pb2 import Twist
from gz.msgs.odometry_pb2 import Odometry

START_X = -105.223
START_Y = -70.77
WORLD_NAME = "default"
MODEL_NAME = "monaco_racing_lights"
LINK_NAME = "lights_link"
RACING_VIS = "racing_light_pods"
TUNNEL_VIS = "tunnel_light_panels"

TUNNEL_ANCHORS = [
    (96.4, 116.6),
    (95.0, 96.0),
    (91.0, 74.0),
    (84.0, 52.0),
    (73.0, 33.0),
    (57.0, 22.8),
]

COLOR_STANDBY_RED = (0.95, 0.08, 0.05, 1.0)
COLOR_RACING_GREEN = (0.04, 1.00, 0.16, 1.0)
COLOR_TUNNEL_DIM = (0.45, 0.45, 0.42, 1.0)
COLOR_TUNNEL_BRIGHT = (1.00, 0.99, 0.94, 1.0)


class RacingLightsController:
    def __init__(self):
        self.node = gzt.Node()
        self.lock = threading.Lock()
        self.race_state = "STANDBY"
        self.tunnel_bright = False
        self.vis_meta = {}  # vis_name -> (id, parent_id)
        self.last_cmd_time = 0.0
        self.last_odom_check = 0.0
        self.stopped_at_start_since = None

        self.mat_pub = self.node.advertise(
            f"/world/{WORLD_NAME}/material_color", MaterialColor
        )
        self.node.subscribe(Twist, "/f1/cmd_vel", self._on_cmd_vel)
        self.node.subscribe(Odometry, "/f1/odom", self._on_odom)

    def discover_scene(self):
        req = Empty()
        ok, resp = self.node.request(
            f"/world/{WORLD_NAME}/scene/info", req, Empty, Scene, 2000
        )
        if not ok or resp is None:
            return False
        for model in resp.model:
            if model.name == MODEL_NAME:
                for link in model.link:
                    for vis in link.visual:
                        if vis.name in (RACING_VIS, TUNNEL_VIS):
                            self.vis_meta[vis.name] = (vis.id, vis.parent_id)
        return RACING_VIS in self.vis_meta

    def set_visual_color(self, vis_name, rgba):
        if vis_name not in self.vis_meta:
            self.discover_scene()
        r, g, b, a = rgba
        if vis_name in self.vis_meta:
            vis_id, parent_id = self.vis_meta[vis_name]
            vmsg = Visual()
            vmsg.id = vis_id
            vmsg.name = vis_name
            vmsg.parent_id = parent_id
            for ch in (
                vmsg.material.ambient,
                vmsg.material.diffuse,
                vmsg.material.emissive,
            ):
                ch.r, ch.g, ch.b, ch.a = r, g, b, a
            vmsg.material.specular.r = 0.35
            vmsg.material.specular.g = 0.35
            vmsg.material.specular.b = 0.35
            vmsg.material.specular.a = 1.0
            try:
                self.node.request(
                    f"/world/{WORLD_NAME}/visual_config", vmsg, Visual, Boolean, 400
                )
            except Exception:
                pass

        mc = MaterialColor()
        mc.entity.name = f"{MODEL_NAME}::{LINK_NAME}::{vis_name}"
        mc.entity_match = MaterialColor.ALL
        for ch in (mc.ambient, mc.diffuse, mc.emissive):
            ch.r, ch.g, ch.b, ch.a = r, g, b, a
        mc.specular.r = 0.35
        mc.specular.g = 0.35
        mc.specular.b = 0.35
        mc.specular.a = 1.0
        self.mat_pub.publish(mc)

    def _on_cmd_vel(self, msg):
        if abs(msg.linear.x) + abs(msg.linear.y) + abs(msg.angular.z) > 0.02:
            with self.lock:
                self.last_cmd_time = time.monotonic()
                if self.race_state != "RACING":
                    self.race_state = "RACING"
                    self.stopped_at_start_since = None
                    threading.Thread(
                        target=self.set_visual_color,
                        args=(RACING_VIS, COLOR_RACING_GREEN),
                        daemon=True,
                    ).start()

    def _on_odom(self, msg):
        # Throttle odom processing to 5 Hz for near-zero CPU usage
        now = time.monotonic()
        if (now - self.last_odom_check) < 0.20:
            return
        self.last_odom_check = now

        spd = math.hypot(msg.twist.linear.x, msg.twist.linear.y)
        px, py = msg.pose.position.x, msg.pose.position.y
        dist_start = math.hypot(px - START_X, py - START_Y)
        dist_tunnel = min(math.hypot(px - tx, py - ty) for tx, ty in TUNNEL_ANCHORS)

        with self.lock:
            if self.race_state == "STANDBY":
                if spd > 0.08 or dist_start > 0.45:
                    self.race_state = "RACING"
                    self.stopped_at_start_since = None
                    threading.Thread(
                        target=self.set_visual_color,
                        args=(RACING_VIS, COLOR_RACING_GREEN),
                        daemon=True,
                    ).start()
            elif self.race_state == "RACING":
                if dist_start < 1.5 and spd < 0.02 and (now - self.last_cmd_time) > 1.5:
                    if self.stopped_at_start_since is None:
                        self.stopped_at_start_since = now
                    elif (now - self.stopped_at_start_since) > 1.5:
                        self.race_state = "STANDBY"
                        self.stopped_at_start_since = None
                        threading.Thread(
                            target=self.set_visual_color,
                            args=(RACING_VIS, COLOR_STANDBY_RED),
                            daemon=True,
                        ).start()
                else:
                    self.stopped_at_start_since = None

            want_bright = dist_tunnel < 26.0
            if want_bright != self.tunnel_bright:
                self.tunnel_bright = want_bright
                col = COLOR_TUNNEL_BRIGHT if want_bright else COLOR_TUNNEL_DIM
                threading.Thread(
                    target=self.set_visual_color, args=(TUNNEL_VIS, col), daemon=True
                ).start()

    def run(self):
        for _ in range(60):
            if self.discover_scene():
                print(
                    f"[racing_lights_controller] Ready with merged visuals: {list(self.vis_meta.keys())}",
                    flush=True,
                )
                self.set_visual_color(RACING_VIS, COLOR_STANDBY_RED)
                self.set_visual_color(TUNNEL_VIS, COLOR_TUNNEL_DIM)
                break
            time.sleep(0.5)

        while True:
            time.sleep(2.0)
            if RACING_VIS not in self.vis_meta:
                if self.discover_scene():
                    self.set_visual_color(
                        RACING_VIS,
                        (
                            COLOR_RACING_GREEN
                            if self.race_state == "RACING"
                            else COLOR_STANDBY_RED
                        ),
                    )
                    self.set_visual_color(
                        TUNNEL_VIS,
                        COLOR_TUNNEL_BRIGHT if self.tunnel_bright else COLOR_TUNNEL_DIM,
                    )


if __name__ == "__main__":
    RacingLightsController().run()
