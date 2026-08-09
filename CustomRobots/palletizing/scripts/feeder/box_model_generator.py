#!/usr/bin/env python3
"""Generate temporary Gazebo SDF models for SKU boxes."""

from pathlib import Path
from typing import Any


def cuboid_inertia(size: list[float], mass: float) -> tuple[float, float, float]:
    length, width, height = size
    ixx = mass * (width * width + height * height) / 12.0
    iyy = mass * (length * length + height * height) / 12.0
    izz = mass * (length * length + width * width) / 12.0
    return ixx, iyy, izz


def make_box_sdf(name: str, size: list[float], mass: float, color: list[float]) -> str:
    length, width, height = size
    r, g, b, a = color
    ixx, iyy, izz = cuboid_inertia(size, mass)

    return f'''<?xml version="1.0" ?>
<sdf version="1.8">
  <model name="{name}">
    <link name="link">
      <gravity>true</gravity>
      <inertial>
        <mass>{mass:.6f}</mass>
        <inertia>
          <ixx>{ixx:.6f}</ixx>
          <ixy>0</ixy>
          <ixz>0</ixz>
          <iyy>{iyy:.6f}</iyy>
          <iyz>0</iyz>
          <izz>{izz:.6f}</izz>
        </inertia>
      </inertial>
      <collision name="collision">
        <geometry>
          <box>
            <size>{length:.6f} {width:.6f} {height:.6f}</size>
          </box>
        </geometry>
        <surface>
          <contact>
            <ode>
              <kp>100000</kp>
              <kd>10</kd>
            </ode>
          </contact>
          <friction>
            <ode>
              <mu>0.8</mu>
              <mu2>0.8</mu2>
            </ode>
          </friction>
        </surface>
      </collision>
      <visual name="visual">
        <geometry>
          <box>
            <size>{length:.6f} {width:.6f} {height:.6f}</size>
          </box>
        </geometry>
        <material>
          <ambient>{r:.6f} {g:.6f} {b:.6f} {a:.6f}</ambient>
          <diffuse>{r:.6f} {g:.6f} {b:.6f} {a:.6f}</diffuse>
          <specular>0.05 0.05 0.05 1</specular>
        </material>
      </visual>
    </link>
  </model>
</sdf>
'''


class BoxModelGenerator:
    def __init__(self, directory: str):
        self.directory = Path(directory)

    def write_model(self, box: dict[str, Any]) -> str:
        path = self.directory / f"{box['name']}.sdf"
        sdf = make_box_sdf(box["name"], box["size"], box["mass"], box["color"])
        path.write_text(sdf, encoding="utf-8")
        return str(path)
