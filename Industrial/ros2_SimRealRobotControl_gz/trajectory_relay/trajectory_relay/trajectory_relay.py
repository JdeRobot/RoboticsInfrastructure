import rclpy

from rclpy.node import Node
from rclpy.action import ActionServer, ActionClient

from control_msgs.action import FollowJointTrajectory


class TrajectoryRelay(Node):

    def __init__(self):

        super().__init__("trajectory_relay")

        self.get_logger().info("Starting trajectory relay...")

        self._server = ActionServer(
            self,
            FollowJointTrajectory,
            "trajectory_relay/follow_joint_trajectory",
            execute_callback=self.execute_callback,
        )

        self._gazebo_client = ActionClient(
            self,
            FollowJointTrajectory,
            "/joint_trajectory_controller/follow_joint_trajectory",
        )

        self.get_logger().info("Trajectory relay ready.")

    async def execute_callback(self, goal_handle):

        self.get_logger().info("Received trajectory.")

        if not self._gazebo_client.wait_for_server(timeout_sec=5.0):

            self.get_logger().error(
                "Gazebo controller not available."
            )

            goal_handle.abort()

            result = FollowJointTrajectory.Result()

            return result

        self.get_logger().info("Sending trajectory to Gazebo...")

        future = self._gazebo_client.send_goal_async(
            goal_handle.request
        )

        goal = await future

        result_future = goal.get_result_async()

        result = await result_future

        goal_handle.succeed()

        return result.result


def main():

    rclpy.init()

    node = TrajectoryRelay()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == "__main__":
    main()