#!/usr/bin/env python3
import random
import os
from gz.msgs10.entity_factory_pb2 import EntityFactory
from ament_index_python.packages import get_package_share_directory
from gz.msgs10.entity_pb2 import Entity
from gz.msgs10.boolean_pb2 import Boolean
from gz.transport13 import Node
import numpy as np


class CarSpawner(object):
    def __init__(self):
        self.node = Node()
        self.active_models = {}
        self.sdf_path = "model://hatchback/model.sdf"
        self.world = "default"
        self.last_spawn = None
        self.spawn_interval = 15.0
        self.lifetime = 35.0
        self.spawn_positions = [
            (-2.5, 20.0, 0.1, -1.57),
            (20.0, 2.5, 0.1, 3.14),
            (-20.0, -2.5, 0.1, 0),
        ]

    def update(self, info, _ecm):
        if info.paused:
            return

        current_time = info.sim_time.total_seconds()

        # Spawn new car
        if (
            self.last_spawn is None
            or current_time - self.last_spawn >= self.spawn_interval
        ):
            coords = random.choice(self.spawn_positions)
            model_name = f"car_{random.randint(1000,9999)}"

            yaw = coords[3]
            qx, qy, qz, qw = etoq(yaw, 0, 0)

            req = EntityFactory()

            req.relative_to = ""
            req.sdf_filename = self.sdf_path
            req.name = model_name
            req.pose.position.x = coords[0]
            req.pose.position.y = coords[1]
            req.pose.position.z = coords[2]
            req.pose.orientation.w = qw
            req.pose.orientation.x = qx
            req.pose.orientation.y = qy
            req.pose.orientation.z = qz

            self.node.request(
                f"/world/{self.world}/create", req, EntityFactory, Boolean, 1000
            )

            self.active_models[model_name] = current_time
            self.last_spawn = current_time
            print(f"Spawned {model_name}")

        # Remove old cars
        for name, spawn_time in list(self.active_models.items()):
            if current_time - spawn_time > self.lifetime:
                self.node.request(
                    f"/world/{self.world}/remove",
                    Entity(name=name, type=Entity.MODEL),
                    Entity,
                    Boolean,
                    1000,
                )
                del self.active_models[name]
                print(f"Removed {name}")

    #reset callback function
    def reset(self, info, _ecm):
        self.active_models.clear()
        self.last_spawn = None


def etoq(yaw, pitch, roll):

    cy = np.cos(yaw * 0.5)
    sy = np.sin(yaw * 0.5)
    cp = np.cos(pitch * 0.5)
    sp = np.sin(pitch * 0.5)
    cr = np.cos(roll * 0.5)
    sr = np.sin(roll * 0.5)

    qw = cr * cp * cy + sr * sp * sy
    qx = sr * cp * cy - cr * sp * sy
    qy = cr * sp * cy + sr * cp * sy
    qz = cr * cp * sy - sr * sp * cy

    return qx, qy, qz, qw


def get_system():
    return CarSpawner()
