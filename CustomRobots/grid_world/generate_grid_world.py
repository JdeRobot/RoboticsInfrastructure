#!/usr/bin/env python3
"""Build a Gazebo grid world for the TurtleBot3 Burger from a text matrix.

Each map file holds one row of cells per line as seen from above.
Lines starting with # are ignored.

    0  free cell
    1  box in the middle of the cell
    2  block that fills the whole cell
    3  thin wall through the cell center joined to neighbour 2 and 3 cells
    R  free base cell where the robot starts facing away from the closest wall

    python3 generate_grid_world.py maps/udc_fig3.txt --name udc_grid_fig3
    python3 generate_grid_world.py maps/udc_fig3.txt --name udc_grid_fig3_lab --style lab
"""

import argparse
import math
import os
import sys

RI_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEXTURES = "model://grid_world_assets/materials/textures"

# Sizes in meters so the LDS at 0.18 m sees every obstacle
STYLES = {
    "webots": {
        "floor_tiles": ("wood_dark.png", "wood_light.png"),
        "outer_floor": None,
        "border": {"thickness": 0.06, "height": 0.3, "texture": "wood_frame.png"},
        "border_cap": None,
        "box": {"size": 0.34, "texture": "cardboard.png", "color": None},
        "block": {"size": 0.38, "color": (0.97, 0.97, 0.97)},
        "wall": {"thickness": 0.02, "height": 0.3, "color": (0.95, 0.95, 0.93)},
    },
    "lab": {
        "floor_tiles": None,
        "outer_floor": "terrazzo.png",
        "border": {"thickness": 0.03, "height": 0.4, "color": (0.95, 0.95, 0.94)},
        "border_cap": {"width": 0.07, "height": 0.02, "texture": "wood_plank.png"},
        "box": {"size": 0.36, "texture": None, "color": (0.93, 0.93, 0.92)},
        "block": {"size": 0.38, "color": (0.93, 0.93, 0.92)},
        "wall": {"thickness": 0.03, "height": 0.4, "color": (0.93, 0.93, 0.92)},
    },
}


def read_map(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if line:
                rows.append(line.split())
    if not rows or any(len(r) != len(rows[0]) for r in rows):
        sys.exit(f"{path}: every row must have the same number of cells")
    for r in rows:
        for c in r:
            if c not in ("0", "1", "2", "3", "R"):
                sys.exit(f"{path}: unknown cell code '{c}'")
    if sum(r.count("R") for r in rows) > 1:
        sys.exit(f"{path}: only one R cell is allowed")
    return rows


class Grid:
    def __init__(self, rows, cell):
        self.rows = rows
        self.n_rows = len(rows)
        self.n_cols = len(rows[0])
        self.cell = cell

    def center(self, r, c):
        x = (c - (self.n_cols - 1) / 2) * self.cell
        y = ((self.n_rows - 1) / 2 - r) * self.cell
        return x, y

    def size(self):
        return self.n_cols * self.cell, self.n_rows * self.cell

    def robot_pose(self):
        for r, row in enumerate(self.rows):
            if "R" in row:
                c = row.index("R")
                break
        else:
            r, c = 0, 0
        x, y = self.center(r, c)
        # Distance in cells to each border wall
        gaps = [r, self.n_rows - 1 - r, c, self.n_cols - 1 - c]
        yaw = (-math.pi / 2, math.pi / 2, 0.0, math.pi)[gaps.index(min(gaps))]
        return x, y, yaw


def material(color=None, texture=None):
    if texture:
        return (
            "<material><ambient>1 1 1 1</ambient><diffuse>1 1 1 1</diffuse>"
            "<pbr><metal>"
            f"<albedo_map>{TEXTURES}/{texture}</albedo_map>"
            "<roughness>0.85</roughness><metalness>0</metalness>"
            "</metal></pbr></material>"
        )
    r, g, b = color
    return (
        f"<material><ambient>{r} {g} {b} 1</ambient>"
        f"<diffuse>{r} {g} {b} 1</diffuse>"
        "<specular>0.1 0.1 0.1 1</specular></material>"
    )


def box_geometry(sx, sy, sz):
    return f"<geometry><box><size>{sx:.4f} {sy:.4f} {sz:.4f}</size></box></geometry>"


def box_element(name, pose, size, mat, collide=True):
    x, y, z = pose
    geom = box_geometry(*size)
    out = f'<visual name="{name}_visual"><pose>{x:.4f} {y:.4f} {z:.4f} 0 0 0</pose>{geom}{mat}</visual>'
    if collide:
        out += f'<collision name="{name}_collision"><pose>{x:.4f} {y:.4f} {z:.4f} 0 0 0</pose>{geom}</collision>'
    return out


def static_model(name, body):
    return (
        f'<model name="{name}"><static>true</static>'
        f'<link name="link">{body}</link></model>'
    )


def floor(grid, style):
    w, h = grid.size()
    parts = []
    if style["floor_tiles"]:
        dark, light = style["floor_tiles"]
        for r in range(grid.n_rows):
            for c in range(grid.n_cols):
                x, y = grid.center(r, c)
                tex = dark if (r + c) % 2 == 0 else light
                parts.append(
                    box_element(
                        f"tile_{r}_{c}",
                        (x, y, 0.001),
                        (grid.cell, grid.cell, 0.002),
                        material(texture=tex),
                        collide=False,
                    )
                )
        parts.append(
            box_element(
                "outer_floor",
                (0, 0, -0.001),
                (w + 3, h + 3, 0.002),
                material(color=(0.55, 0.55, 0.55)),
                collide=False,
            )
        )
    else:
        # Lab floor tiles of 60 cm around and under the grid
        tile = 0.6
        nx, ny = math.ceil((w + 3) / tile), math.ceil((h + 3) / tile)
        for i in range(nx):
            for j in range(ny):
                x = (i - (nx - 1) / 2) * tile
                y = (j - (ny - 1) / 2) * tile
                parts.append(
                    box_element(
                        f"floor_{i}_{j}",
                        (x, y, 0.001),
                        (tile - 0.003, tile - 0.003, 0.002),
                        material(texture=style["outer_floor"]),
                        collide=False,
                    )
                )
        parts.append(
            box_element(
                "floor_joints",
                (0, 0, -0.001),
                (nx * tile, ny * tile, 0.002),
                material(color=(0.18, 0.19, 0.19)),
                collide=False,
            )
        )
    parts.append(
        '<collision name="ground"><geometry><plane><normal>0 0 1</normal>'
        "<size>50 50</size></plane></geometry></collision>"
    )
    return static_model("grid_floor", "".join(parts))


def border(grid, style):
    w, h = grid.size()
    b = style["border"]
    t, hz = b["thickness"], b["height"]
    mat = material(color=b.get("color"), texture=b.get("texture"))
    sides = [
        ("north", (0, h / 2 + t / 2), (w + 2 * t, t)),
        ("south", (0, -h / 2 - t / 2), (w + 2 * t, t)),
        ("east", (w / 2 + t / 2, 0), (t, h)),
        ("west", (-w / 2 - t / 2, 0), (t, h)),
    ]
    parts = []
    for name, (x, y), (sx, sy) in sides:
        parts.append(box_element(name, (x, y, hz / 2), (sx, sy, hz), mat))
        cap = style["border_cap"]
        if cap:
            cw = cap["width"]
            csx = sx + (cw - t) if sx > sy else cw
            csy = sy + (cw - t) if sy > sx else cw
            parts.append(
                box_element(
                    f"{name}_cap",
                    (x, y, hz + cap["height"] / 2),
                    (csx, csy, cap["height"]),
                    material(texture=cap["texture"]),
                )
            )
    return static_model("grid_border", "".join(parts))


def obstacles(grid, style):
    models = []
    for r, row in enumerate(grid.rows):
        for c, code in enumerate(row):
            x, y = grid.center(r, c)
            if code == "1":
                s = style["box"]["size"]
                mat = material(style["box"]["color"], style["box"]["texture"])
                body = box_element("box", (0, 0, s / 2), (s, s, s), mat)
                models.append(
                    f'<model name="box_{r}_{c}"><static>true</static>'
                    f"<pose>{x:.4f} {y:.4f} 0 0 0 0</pose>"
                    f'<link name="link">{body}</link></model>'
                )
            elif code == "2":
                s = style["block"]["size"]
                body = box_element("block", (0, 0, s / 2), (s, s, s), material(style["block"]["color"]))
                models.append(
                    f'<model name="block_{r}_{c}"><static>true</static>'
                    f"<pose>{x:.4f} {y:.4f} 0 0 0 0</pose>"
                    f'<link name="link">{body}</link></model>'
                )
    return "".join(models)


def thin_walls(grid, style):
    wall = style["wall"]
    t, hz = wall["thickness"], wall["height"]
    mat = material(wall["color"])
    parts = []

    def code(r, c):
        if 0 <= r < grid.n_rows and 0 <= c < grid.n_cols:
            return grid.rows[r][c]
        return None

    for r in range(grid.n_rows):
        for c in range(grid.n_cols):
            if code(r, c) != "3":
                continue
            x, y = grid.center(r, c)
            joined = False
            # Segments join two cell centers and overlap at the corners
            for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                other = code(r + dr, c + dc)
                if other not in ("2", "3"):
                    continue
                joined = True
                if other == "3" and (dr, dc) in ((0, -1), (-1, 0)):
                    continue
                ox, oy = grid.center(r + dr, c + dc)
                mx, my = (x + ox) / 2, (y + oy) / 2
                size = (grid.cell + t, t, hz) if dr == 0 else (t, grid.cell + t, hz)
                parts.append(box_element(f"wall_{r}_{c}_{dr}_{dc}", (mx, my, hz / 2), size, mat))
            if not joined:
                parts.append(box_element(f"wall_{r}_{c}", (x, y, hz / 2), (grid.cell, t, hz), mat))
    return static_model("thin_walls", "".join(parts)) if parts else ""


def world_sdf(grid, style, source):
    w, h = grid.size()
    return f"""<?xml version="1.0" ?>
<!-- Generated by generate_grid_world.py from {source} -->
<sdf version="1.9">
  <world name="default">
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>

    <scene>
      <ambient>0.6 0.6 0.6 1</ambient>
      <background>0.8 0.8 0.8 1</background>
      <grid>false</grid>
    </scene>

    <light type="directional" name="sun">
      <cast_shadows>false</cast_shadows>
      <pose>0 0 10 0 0 0</pose>
      <diffuse>0.9 0.9 0.9 1</diffuse>
      <specular>0.2 0.2 0.2 1</specular>
      <direction>-0.3 0.2 -1</direction>
    </light>

    <light type="directional" name="fill">
      <cast_shadows>false</cast_shadows>
      <pose>0 0 10 0 0 0</pose>
      <diffuse>0.45 0.45 0.45 1</diffuse>
      <specular>0 0 0 1</specular>
      <direction>0.6 -0.7 -0.5</direction>
    </light>

    {floor(grid, style)}
    {border(grid, style)}
    {obstacles(grid, style)}
    {thin_walls(grid, style)}
  </world>
</sdf>
"""


def launch_py(name):
    template = os.path.join(RI_ROOT, "Launchers", "small_laser_mapping.launch.py")
    with open(template) as f:
        return f.read().replace("small_laser_mapping.world", f"{name}.world")


def viz_config(name, grid):
    template = os.path.join(RI_ROOT, "Launchers", "visualization", "small_laser_mapping.config")
    with open(template) as f:
        text = f.read()
    w, h = grid.size()
    height = max(w, h) * 1.3 + 1.0
    text = text.replace(
        "<camera_pose>0.0 0.0 8 0 1.57 3.14</camera_pose>",
        f"<camera_pose>0.0 0.0 {height:.1f} 0 1.57 1.5708</camera_pose>",
    )
    return text.replace("<follow_target>waffle</follow_target>", "<follow_target>turtlebot3</follow_target>")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("map", help="text file with the cell matrix")
    parser.add_argument("--name", required=True, help="base name of the generated files")
    parser.add_argument("--style", choices=sorted(STYLES), default="webots")
    parser.add_argument("--cell", type=float, default=0.4, help="cell side in meters")
    parser.add_argument("--root", default=RI_ROOT, help="RoboticsInfrastructure root to write into")
    args = parser.parse_args()

    grid = Grid(read_map(args.map), args.cell)
    style = STYLES[args.style]
    source = os.path.relpath(os.path.abspath(args.map), os.path.dirname(os.path.abspath(__file__)))

    outputs = {
        os.path.join(args.root, "Scenes", f"{args.name}.world"): world_sdf(grid, style, source),
        os.path.join(args.root, "Launchers", f"{args.name}.launch.py"): launch_py(args.name),
        os.path.join(args.root, "Launchers", "visualization", f"{args.name}.config"): viz_config(args.name, grid),
    }
    for path, text in outputs.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)
        print(f"wrote {os.path.relpath(path, args.root)}")

    w, h = grid.size()
    x, y, yaw = grid.robot_pose()
    print(f"\n{grid.n_rows} x {grid.n_cols} cells of {args.cell} m, arena {w:.2f} x {h:.2f} m, style {args.style}")
    for row in grid.rows:
        print("  " + " ".join(row))
    print(f"\nrobot pose for worlds_robots  {{{{{x:.2f},{y:.2f},0.0,0.0,0.0,{yaw:.4f}}}}}")


if __name__ == "__main__":
    main()
