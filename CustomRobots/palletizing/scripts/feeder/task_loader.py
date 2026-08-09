#!/usr/bin/env python3
"""Load and normalize palletizing task configuration."""

from typing import Any

import yaml


class PalletizingTaskConfig:
    def __init__(self, path: str):
        with open(path, "r", encoding="utf-8") as config_file:
            self.data = yaml.safe_load(config_file)
        if not isinstance(self.data, dict):
            raise RuntimeError(f"invalid palletizing task config: {path}")

        self.robot = self.data["robot"]
        self.pallet = self.data["pallet"]
        self.conveyor = self.data["conveyor"]
        self.skus = self.data["boxes"]["skus"]
        self.sequence = list(self.data["boxes"]["sequence"])

    @property
    def box_count(self) -> int:
        return len(self.sequence)

    def box_at(self, index: int, run_id: int) -> dict[str, Any]:
        sku = self.sequence[index]
        if sku not in self.skus:
            raise RuntimeError(f"unknown SKU in sequence: {sku}")

        spec = self.skus[sku]
        size = [float(v) for v in spec["size"]]
        mass = float(spec.get("mass", 2.0))
        color = [float(v) for v in spec.get("color", [0.76, 0.58, 0.36, 1.0])]

        return {
            "name": f"box_{run_id}_{index}",
            "sku": sku,
            "size": size,
            "mass": mass,
            "color": color,
        }

    def box_info(
        self,
        box: dict[str, Any],
        pickup_world_position: dict[str, float],
    ) -> dict[str, Any]:
        """Return box metadata including its observed pickup pose in base_link."""
        base_z = float(self.robot["base_mount_world_z"])
        _, _, height = box["size"]
        pickup_center = [
            float(pickup_world_position["x"]),
            float(pickup_world_position["y"]),
            float(pickup_world_position["z"]) - base_z,
        ]

        return {
            "name": box["name"],
            "sku": box["sku"],
            "size": box["size"],
            "mass": box["mass"],
            "pickup_pose": {
                "frame": "base_link",
                "center": pickup_center,
                "top_z": pickup_center[2] + height / 2.0,
            },
        }

    def pallet_info(self) -> dict[str, Any]:
        base_z = float(self.robot["base_mount_world_z"])
        placement_center = self.pallet.get("usable_center", self.pallet["world_center"])
        placement_center = [float(v) for v in placement_center]
        deck_top_world_z = float(self.pallet["deck_top_world_z"])

        return {
            "frame": "base_link",
            "size": [float(v) for v in self.pallet["physical_size"]],
            "usable_size": [float(v) for v in self.pallet["usable_size"]],
            "center": [placement_center[0], placement_center[1], placement_center[2] - base_z],
            "top_z": deck_top_world_z - base_z,
            "max_layers": int(self.pallet["max_layers"]),
        }

    def spawn_z(self, box: dict[str, Any]) -> float:
        belt_z = float(self.conveyor["belt_surface_world_z"])
        clearance = float(self.conveyor["spawn_clearance"])
        return belt_z + box["size"][2] / 2.0 + clearance
