"""Track dynamic Gazebo model poses for palletizing feeder decisions."""

import time
from threading import Lock
from typing import TypedDict

from gz.msgs10.pose_v_pb2 import Pose_V
from gz.transport13 import Node, SubscribeOptions


class WorldPosition(TypedDict):
    x: float
    y: float
    z: float


class GazeboPoseTracker:
    """Track one active palletizing box without processing every world pose."""

    def __init__(self, world_name: str = "default", sample_period: float = 0.05):
        self._active_model: str | None = None
        self._position: WorldPosition | None = None
        self._sample_period = sample_period
        self._last_sample_time = 0.0
        self._lock = Lock()
        self._node = Node()
        options = SubscribeOptions()
        options.msgs_per_sec = 20
        self._node.subscribe(
            Pose_V,
            f"/world/{world_name}/dynamic_pose/info",
            self._on_pose_update,
            options,
        )

    def track(self, model_name: str) -> None:
        with self._lock:
            self._active_model = model_name
            self._position = None
            self._last_sample_time = 0.0

    def clear(self) -> None:
        with self._lock:
            self._active_model = None
            self._position = None

    def _on_pose_update(self, message: Pose_V) -> None:
        now = time.monotonic()
        with self._lock:
            active_model = self._active_model
            if active_model is None or now - self._last_sample_time < self._sample_period:
                return
            self._last_sample_time = now

        for pose in message.pose:
            if pose.name == active_model:
                position = {
                    "x": float(pose.position.x),
                    "y": float(pose.position.y),
                    "z": float(pose.position.z),
                }
                with self._lock:
                    if self._active_model == active_model:
                        self._position = position
                return

    def position(self, model_name: str) -> WorldPosition | None:
        """Return the latest sampled pose when ``model_name`` is active."""
        with self._lock:
            if model_name != self._active_model or self._position is None:
                return None
            return dict(self._position)
