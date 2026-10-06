#!/usr/bin/env python3
"""Generate the dirt and the cat map of the vacuum cleaner party house.

Slices the collision meshes of house_int2 (walls + furniture) at the robot
height to find the floor the vacuum can actually clean, then writes:
  pieces.txt    confetti and spilled soil for the vacuum_dirt system
  cat_map.pgm   area the cat walks on (dark = free) for the cat_walker system

Development tool only, needs trimesh, pycollada, scipy and pillow:
  python3 generate_party_house.py <custom_robots_dir> <output_dir>
"""

import math
import re
import sys
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw
from scipy import ndimage

RES = 0.01
X0, X1, Y0, Y1 = -4.3, 5.7, -3.9, 6.3
ROBOT_RADIUS = 0.18
ROBOT_HEIGHT = 0.08
ROBOT_START = (-1.0, 1.5)
CAT_CLEARANCE = 0.08
CAT_MAP_RES = 0.05
SEED = 7

# Knocked over plant pot in the living room corner, mouth towards the room
POT = (1.27, 5.72)
POT_RADIUS = 0.3
MUD = (0.92, 5.36)

# Where the party was (x, y, sigma, weight)
HOTSPOTS = [(-0.8, 3.9, 1.3, 10.0), (-2.4, 0.3, 1.0, 5.0), (0.8, 2.0, 1.5, 2.0)]
BASE_DENSITY = 0.6
CONFETTI = 18000
SOIL = 420

# Palette indexes of vacuum_dirt.cpp: 8 colors x 3 shades, then two browns
N_COLORS, N_SHADES = 8, 3
BROWNS = (24, 25)


def px(x, y):
    return (x - X0) / RES, (Y1 - y) / RES


def coverable_floor(models):
    """Floor cells the robot can sweep, reachable from its start pose."""
    W, H = int((X1 - X0) / RES), int((Y1 - Y0) / RES)
    sdf = (models / "house_int2" / "model.sdf").read_text()
    items = [("house_int2", [0.0] * 6)] + [
        (uri, [float(v) for v in pose.split()])
        for uri, pose in re.findall(r"<uri>model://(\w+)</uri>\s*<pose>([^<]+)</pose>", sdf)
    ]

    img = Image.new("L", (W, H), 0)
    draw = ImageDraw.Draw(img)
    for name, (x, y, z, roll, pitch, yaw) in items:
        mesh = trimesh.load(models / name / "meshes" / "model.dae", force="scene").to_geometry()
        mesh.apply_transform(trimesh.transformations.compose_matrix(
            angles=[roll, pitch, yaw], translate=[x, y, z]))
        tri = mesh.triangles
        zmin, zmax = tri[:, :, 2].min(1), tri[:, :, 2].max(1)
        # Triangles crossing the robot height band, walls show up as lines
        for t in tri[(zmax > 0.015) & (zmin < ROBOT_HEIGHT)]:
            draw.polygon([px(*v[:2]) for v in t], fill=255, outline=255)
    cx, cy = px(*POT)
    r = POT_RADIUS / RES
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)

    obstacles = np.array(img) > 0
    k = int(ROBOT_RADIUS / RES)
    yy, xx = np.mgrid[-k:k + 1, -k:k + 1]
    disk = xx ** 2 + yy ** 2 <= k * k
    labels, _ = ndimage.label(~ndimage.binary_dilation(obstacles, disk))
    sx, sy = px(*ROBOT_START)
    reachable = labels == labels[int(sy), int(sx)]
    return ndimage.binary_dilation(reachable, disk) & ~obstacles


def main():
    models = Path(sys.argv[1]) / "roomba_robot" / "models"
    out = Path(sys.argv[2])
    rng = np.random.default_rng(SEED)
    cover = coverable_floor(models)
    H, W = cover.shape

    def free(x, y):
        c, r = int((x - X0) / RES), int((Y1 - y) / RES)
        return 0 <= r < H and 0 <= c < W and cover[r, c]

    def density(x, y):
        return BASE_DENSITY + sum(
            w * math.exp(-((x - hx) ** 2 + (y - hy) ** 2) / (2 * s * s)) for hx, hy, s, w in HOTSPOTS)

    def random_point():
        return rng.uniform(X0, X1), rng.uniform(Y0, Y1)

    dmax = BASE_DENSITY + sum(h[3] for h in HOTSPOTS)
    points = []
    while len(points) < CONFETTI * 0.8:
        x, y = random_point()
        if free(x, y) and rng.uniform() < density(x, y) / dmax:
            points.append((x, y))
    # Small clumps, the kind that piles up by walls and furniture
    while len(points) < CONFETTI:
        x, y = random_point()
        if not free(x, y) or rng.uniform() > density(x, y) / dmax + 0.15:
            continue
        s = rng.uniform(0.05, 0.18)
        for _ in range(rng.integers(15, 50)):
            cx, cy = x + rng.normal(0, s), y + rng.normal(0, s)
            if free(cx, cy):
                points.append((cx, cy))

    lines = []
    for x, y in points:
        color = int(rng.integers(N_COLORS)) * N_SHADES + int(rng.integers(N_SHADES))
        yaw = rng.uniform(0, 2 * math.pi)
        kind = rng.uniform()
        if kind < 0.55:
            lines.append(f"confetti rect {x:.4f} {y:.4f} {yaw:.3f} "
                         f"{rng.uniform(0.015, 0.026):.4f} {rng.uniform(0.010, 0.020):.4f} {color}")
        elif kind < 0.92:
            d = rng.uniform(0.014, 0.024)
            lines.append(f"confetti disc {x:.4f} {y:.4f} 0 {d:.4f} {d:.4f} {color}")
        else:
            # Curly streamer as a few bent segments
            seg = rng.uniform(0.03, 0.05)
            cx, cy, a = x, y, yaw
            for _ in range(rng.integers(2, 5)):
                mx, my = cx + math.cos(a) * seg / 2, cy + math.sin(a) * seg / 2
                if free(mx, my):
                    lines.append(f"confetti rect {mx:.4f} {my:.4f} {a:.3f} {seg:.4f} 0.0045 {color}")
                cx, cy = cx + math.cos(a) * seg, cy + math.sin(a) * seg
                a += rng.normal(0, 0.9)

    # Soil fanning out of the pot mouth, thinner the further it went
    axis = math.atan2(MUD[1] - POT[1], MUD[0] - POT[0])
    soil = 0
    while soil < SOIL:
        dist = POT_RADIUS * 0.4 + abs(rng.normal(0, 0.28))
        a = axis + rng.normal(0, 0.45)
        x, y = POT[0] + dist * math.cos(a), POT[1] + dist * math.sin(a)
        if not free(x, y):
            continue
        d = rng.uniform(0.006, 0.016)
        shape = "disc" if rng.uniform() < 0.6 else "rect"
        lines.append(f"soil {shape} {x:.4f} {y:.4f} {rng.uniform(0, 6.28):.3f} "
                     f"{d:.4f} {d * rng.uniform(0.6, 1.0):.4f} {BROWNS[int(rng.integers(2))]}")
        soil += 1

    out.mkdir(parents=True, exist_ok=True)
    with open(out / "pieces.txt", "w") as f:
        f.write("# category shape x y yaw size_x size_y color\n")
        f.write("\n".join(lines) + "\n")

    # The cat keeps off the walls but always walks where the robot can clean
    k = int(CAT_CLEARANCE / RES)
    yy, xx = np.mgrid[-k:k + 1, -k:k + 1]
    walk = ndimage.binary_erosion(cover, xx ** 2 + yy ** 2 <= k * k)
    step = int(round(CAT_MAP_RES / RES))
    hh, ww = (H // step) * step, (W // step) * step
    coarse = walk[:hh, :ww].reshape(hh // step, step, ww // step, step).all(axis=(1, 3))
    # Keep only the area connected to the mud spot so every goal is reachable
    mud_c, mud_r = int((MUD[0] - X0) / CAT_MAP_RES), int((Y1 - MUD[1]) / CAT_MAP_RES)
    assert coarse[mud_r, mud_c], "the mud spot must be walkable"
    labels, _ = ndimage.label(coarse)
    coarse = labels == labels[mud_r, mud_c]
    Image.fromarray(np.where(coarse, 0, 255).astype(np.uint8)).save(out / "cat_map.pgm")
    print(f"pieces {len(lines)}  cat map origin_x {X0} origin_y {Y1 - coarse.shape[0] * CAT_MAP_RES:.2f}")


if __name__ == "__main__":
    main()
