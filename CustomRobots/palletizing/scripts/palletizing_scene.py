#!/usr/bin/env python3
"""Publish static conveyor and pallet obstacles in MoveIt's base_link frame.

Dynamic, carried, and placed boxes are not modeled.
"""

import rclpy
from geometry_msgs.msg import Pose
from moveit_msgs.msg import CollisionObject, PlanningScene
from moveit_msgs.srv import ApplyPlanningScene
from rclpy.node import Node
from shape_msgs.msg import SolidPrimitive

BASE_MOUNT_Z = 0.9        # world z of robot base_link; must match the world file
PLANNING_FRAME = "base_link"


def _world_to_base_z(world_z):
    return world_z - BASE_MOUNT_Z


# Gazebo world geometry; keep synchronized with the scene.
# The pallet collision ends below the deck top to allow flush placement.
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

        self._client = self.create_client(
            ApplyPlanningScene,
            "/apply_planning_scene",
        )

        self._scene = PlanningScene()
        self._scene.is_diff = True
        for spec in OBSTACLES:
            self._scene.world.collision_objects.append(_make_collision_object(spec))

    def apply(self, timeout_sec=30.0):
        obstacle_ids = [obj.id for obj in self._scene.world.collision_objects]
        self.get_logger().info(
            "waiting for MoveIt /apply_planning_scene service to apply "
            f"{obstacle_ids} in frame '{PLANNING_FRAME}'"
        )

        if not self._client.wait_for_service(timeout_sec=timeout_sec):
            raise RuntimeError(
                "MoveIt /apply_planning_scene service unavailable after "
                f"{timeout_sec:.1f}s"
            )

        request = ApplyPlanningScene.Request()
        request.scene = self._scene
        future = self._client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=timeout_sec)

        if not future.done():
            raise RuntimeError(
                "timed out while applying the palletizing planning scene"
            )

        if future.exception() is not None:
            raise RuntimeError(
                "failed to apply the palletizing planning scene: "
                f"{future.exception()}"
            )

        response = future.result()
        if response is None or not response.success:
            raise RuntimeError("MoveIt rejected the palletizing planning scene")

        self.get_logger().info(
            f"confirmed MoveIt planning-scene objects: {obstacle_ids}"
        )


def main():
    rclpy.init()
    node = PalletizingScene()
    try:
        node.apply()
    except Exception as error:
        node.get_logger().fatal(str(error))
        raise
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
