#!/usr/bin/env python3
"""Palletizing planning-scene publisher (behind the scenes — not student-facing).

Injects the static workcell obstacles (conveyor, pallet) into MoveIt's planning
scene so the planner routes around them, instead of hand-tuning via-waypoints in
the exercise code. Publishes a PlanningScene diff on /planning_scene (which
move_group subscribes to), transient_local and repeated a few times so a
late-starting move_group still receives it.

Objects are given in Gazebo world coordinates and published in `base_link` (the
frame the robot's motion targets use); base_link sits at world z = BASE_MOUNT_Z.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSReliabilityPolicy

from moveit_msgs.msg import PlanningScene, CollisionObject
from shape_msgs.msg import SolidPrimitive
from geometry_msgs.msg import Pose

BASE_MOUNT_Z = 0.9        # robot base height in world; must match the world file
PLANNING_FRAME = "base_link"


def _world_to_base_z(world_z):
    return world_z - BASE_MOUNT_Z


# Workcell obstacles in Gazebo world coordinates (matching the model SDFs).
# The pallet box is trimmed ~3 cm below the real deck top (world 0.30 -> 0.27) so a
# box placed flush on the deck isn't rejected as a touching-contact collision.
OBSTACLES = [
    {
        "id": "conveyor",
        "size": [2.4, 0.8, 0.1],
        "world_xyz": [1.80, 0.0, 0.95],
    },
    {
        "id": "pallet",
        "size": [1.60, 1.30, 0.27],
        "world_xyz": [0.0, -0.88, 0.135],
    },
]


def _make_collision_object(spec):
    obj = CollisionObject()
    obj.header.frame_id = PLANNING_FRAME
    obj.id = spec["id"]

    box = SolidPrimitive()
    box.type = SolidPrimitive.BOX
    box.dimensions = list(spec["size"])

    pose = Pose()
    wx, wy, wz = spec["world_xyz"]
    pose.position.x = float(wx)
    pose.position.y = float(wy)
    pose.position.z = float(_world_to_base_z(wz))
    pose.orientation.w = 1.0

    obj.primitives.append(box)
    obj.primitive_poses.append(pose)
    obj.operation = CollisionObject.ADD
    return obj


class PalletizingScene(Node):
    def __init__(self):
        super().__init__("palletizing_scene")

        qos = QoSProfile(depth=1)
        qos.durability = QoSDurabilityPolicy.TRANSIENT_LOCAL
        qos.reliability = QoSReliabilityPolicy.RELIABLE

        self._pub = self.create_publisher(PlanningScene, "/planning_scene", qos)

        self._scene = PlanningScene()
        self._scene.is_diff = True
        for spec in OBSTACLES:
            self._scene.world.collision_objects.append(_make_collision_object(spec))

        # Republish a few times so the scene monitor catches it regardless of
        # start-up ordering, then stop; the objects persist in the scene.
        self._count = 0
        self._max_publishes = 5
        self._timer = self.create_timer(1.0, self._publish_once)
        self.get_logger().info(
            f"palletizing_scene: publishing {len(OBSTACLES)} obstacle(s) "
            f"[{', '.join(o['id'] for o in OBSTACLES)}] to /planning_scene "
            f"in frame '{PLANNING_FRAME}'"
        )

    def _publish_once(self):
        self._pub.publish(self._scene)
        self._count += 1
        if self._count >= self._max_publishes:
            self.get_logger().info(
                "palletizing_scene: obstacles injected; done republishing."
            )
            self._timer.cancel()


def main():
    try:
        rclpy.init()
    except RuntimeError:
        pass
    node = PalletizingScene()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
