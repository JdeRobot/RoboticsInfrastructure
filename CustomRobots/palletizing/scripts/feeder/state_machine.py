#!/usr/bin/env python3
"""ROS-independent palletizing feeder state."""

from enum import Enum
from typing import Any


class FeederState(Enum):
    IDLE = "idle"
    MOVING_TO_PICKUP = "moving_to_pickup"
    SETTLING = "settling"
    READY = "ready"
    DONE = "done"


class BoxFeederStateMachine:
    def __init__(self, total_boxes: int):
        self.total_boxes = total_boxes
        self.index = 0
        self.state = FeederState.IDLE
        self.pending_box: dict[str, Any] | None = None

    def has_next_box(self) -> bool:
        return self.index < self.total_boxes

    def begin_spawn(self, box: dict[str, Any]) -> None:
        self.pending_box = box
        self.index += 1
        self.state = FeederState.MOVING_TO_PICKUP

    def reached_pickup(self) -> None:
        self.state = FeederState.SETTLING

    def ready(self) -> None:
        self.state = FeederState.READY

    def accept_done(self, name: str) -> bool:
        if self.pending_box is None or name != self.pending_box["name"]:
            return False
        self.pending_box = None
        self.state = FeederState.IDLE if self.has_next_box() else FeederState.DONE
        return True

    def expected_name(self) -> str | None:
        return self.pending_box["name"] if self.pending_box else None
