#!/usr/bin/env python3
import random
import time
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
        self.last_spawn_time = 0.0
        self.last_iterations = 0
        self.sdf_path = "model://hatchback/model.sdf"
        self.world = "default"
        self.spawn_interval = 15.0
        self.lifetime = 35.0
        self.spawn_positions = [
            (-2.5, 20.0, 0.1, -1.57),
            (20.0, 2.5, 0.1, 3.14),
            (-20.0, -2.5, 0.1, 0),
        ]

    def update(self, info, _ecm):
        current_iterations = info.iterations
        
        # We can approximate sim_time using iterations if we assume a fixed timestep of 0.001 (default)
        # Alternatively, info.sim_time could be used, but iterations is a very safe fallback.
                # Safely get current simulation time
        if hasattr(info, 'sim_time'):
            if hasattr(info.sim_time, 'total_seconds'):
                current_sim_time = info.sim_time.total_seconds()
            else:
                # In some older bindings it might be a float
                current_sim_time = float(info.sim_time)
        else:
            current_sim_time = current_iterations * 0.001 

        if current_iterations < self.last_iterations:
            # Simulation reset detected!
            print("Simulation reset detected. Clearing active models to prevent ghost artifacts.")
            for name in list(self.active_models.keys()):
                # Remove from Gazebo explicitly
                self.node.request(
                    f"/world/{self.world}/remove",
                    Entity(name=name, type=Entity.MODEL),
                    Entity,
                    Boolean,
                    1000,
                )
            self.active_models.clear()
            self.last_spawn_time = current_sim_time
            self.last_iterations = current_iterations
            return

        self.last_iterations = current_iterations

        # Spawn new car based on sim time
        if current_sim_time - self.last_spawn_time > self.spawn_interval:
            coords = random.choice(self.spawn_positions)
            model_name = f"car_{random.randint(1000,99999)}"

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

            self.active_models[model_name] = current_sim_time
            self.last_spawn_time = current_sim_time
            print(f"Spawned {model_name} at sim time {current_sim_time:.1f}")

        # Remove old cars based on sim time
        for name, spawn_time in list(self.active_models.items()):
            if current_sim_time - spawn_time > self.lifetime:
                self.node.request(
                    f"/world/{self.world}/remove",
                    Entity(name=name, type=Entity.MODEL),
                    Entity,
                    Boolean,
                    1000,
                )
                del self.active_models[name]
                print(f"Removed {name} at sim time {current_sim_time:.1f}")


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
