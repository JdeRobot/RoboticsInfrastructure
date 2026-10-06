#!/usr/bin/env python3
# Builds the carry and stand animations from meshes/walk.dae
# Only the joint curves change so every file keeps the same skeleton
import os
import re
import xml.etree.ElementTree as ET

import numpy as np

MESHES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "meshes")
NS = "{http://www.collada.org/2005/11/COLLADASchema}"

# Wrist targets on the box sides that kCarryAhead and kCarryZ in warehouse_workers.cpp follow
AHEAD = 0.35
HALF_WIDTH = 0.23
HAND_Z = 1.0
# Walk frame that gives the upper body of the still pose
STAND_FRAME = 35
LEGS = ["LHipJoint", "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase",
        "RHipJoint", "RightUpLeg", "RightLeg", "RightFoot", "RightToeBase"]


def load(path):
    root = ET.parse(path).getroot()
    joints, order, ids = {}, [], {}

    def visit(node, parent):
        if node.get("type") == "JOINT":
            name = node.get("sid")
            ids[node.get("id")] = name
            matrix = np.array(node.find(NS + "matrix").text.split(), float).reshape(4, 4)
            joints[name] = {"parent": parent, "bind": matrix}
            order.append(name)
            parent = name
        for child in node.findall(NS + "node"):
            visit(child, parent)

    for scene in root.iter(NS + "visual_scene"):
        for node in scene.findall(NS + "node"):
            visit(node, None)

    anims = {}
    for anim in root.iter(NS + "animation"):
        channel = anim.find(NS + "channel")
        if channel is None:
            continue
        sources = {s.get("id"): s for s in anim.findall(NS + "source")}
        inputs = {i.get("semantic"): i.get("source")[1:]
                  for i in anim.find(NS + "sampler").findall(NS + "input")}
        out = sources[inputs["OUTPUT"]].find(NS + "float_array")
        name = ids[channel.get("target").split("/")[0]]
        anims[name] = {"id": out.get("id"),
                       "M": np.array(out.text.split(), float).reshape(-1, 4, 4)}
    return joints, order, anims


def forward(joints, order, local):
    world = {}
    for j in order:
        parent = joints[j]["parent"]
        world[j] = (world[parent] if parent else np.eye(4)) @ local[j]
    return world


def rotation_between(a, b):
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    v = np.cross(a, b)
    c = np.dot(a, b)
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3)
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + k + k @ k * ((1 - c) / np.dot(v, v))


joints, order, anims = load(os.path.join(MESHES, "walk.dae"))
frames = len(anims["Hips"]["M"])
hips_y = np.mean(anims["Hips"]["M"][:, 1, 3])


def frame(k):
    return {j: (anims[j]["M"][k] if j in anims else joints[j]["bind"]).copy() for j in order}


def hold_box(local):
    """Two bone IK of both arms with the elbows down and out."""
    world = forward(joints, order, local)
    hips_x = world["Hips"][0, 3]
    for side, sign in (("Left", 1), ("Right", -1)):
        arm, fore, hand = side + "Arm", side + "ForeArm", side + "Hand"
        shoulder = world[arm][:3, 3]
        upper = np.linalg.norm(local[fore][:3, 3])
        lower = np.linalg.norm(local[hand][:3, 3])
        target = np.array([hips_x + AHEAD, hips_y + sign * HALF_WIDTH, HAND_Z])
        u = (target - shoulder) / np.linalg.norm(target - shoulder)
        d = min(np.linalg.norm(target - shoulder), upper + lower - 1e-3)
        pole = np.array([-0.4, sign * 0.6, -1.0])
        v = pole - np.dot(pole, u) * u
        v /= np.linalg.norm(v)
        angle = np.arccos(np.clip((upper**2 + d**2 - lower**2) / (2 * upper * d), -1, 1))
        elbow = shoulder + upper * (np.cos(angle) * u + np.sin(angle) * v)
        wrist = shoulder + d * u

        parent = world[joints[arm]["parent"]]
        arm_world = parent @ local[arm]
        arm_world[:3, :3] = rotation_between(arm_world[:3, :3] @ local[fore][:3, 3],
                                             elbow - shoulder) @ arm_world[:3, :3]
        arm_local = np.linalg.inv(parent) @ arm_world
        arm_local[:3, 3] = local[arm][:3, 3]
        local[arm] = arm_local
        arm_world = parent @ arm_local

        fore_world = arm_world @ local[fore]
        fore_world[:3, :3] = rotation_between(fore_world[:3, :3] @ local[hand][:3, 3],
                                              wrist - elbow) @ fore_world[:3, :3]
        fore_local = np.linalg.inv(arm_world) @ fore_world
        fore_local[:3, 3] = local[fore][:3, 3]
        local[fore] = fore_local
    return local


def stand():
    local = frame(STAND_FRAME)
    hips = joints["Hips"]["bind"].copy()
    hips[:3, 3] = [0.0, hips_y, local["Hips"][2, 3]]
    local["Hips"] = hips
    for j in LEGS:
        local[j] = joints[j]["bind"].copy()
    return local


def write(name, poses):
    text = open(os.path.join(MESHES, "walk.dae")).read()
    for j, anim in anims.items():
        values = " ".join("%.7g" % v for pose in poses for v in pose[j].reshape(-1))
        pattern = r'(<float_array id="%s"[^>]*>)[^<]*(</float_array>)' % re.escape(anim["id"])
        text, count = re.subn(pattern, lambda m: m.group(1) + values + m.group(2), text)
        assert count == 1, anim["id"]
    open(os.path.join(MESHES, name), "w").write(text)


write("carry.dae", [hold_box(frame(k)) for k in range(frames)])
write("stand.dae", [stand() for _ in range(frames)])
write("stand_carry.dae", [hold_box(stand()) for _ in range(frames)])
