import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from amazon_robot_msg.action import FollowTargets
from geometry_msgs.msg import PoseStamped

class FollowTargetActionClient(Node):

    def __init__(self):
        super().__init__('follow_target_action_client')
        self._action_client = ActionClient(self, FollowTargets, '/robot1/FollowTargets')


    def send_goal(self, pose):
        goal_msg = FollowTargets.Goal()
        pose_stamped = PoseStamped()
        pose_stamped.pose.position.x = -5.10
        pose_stamped.pose.position.y = -3.98
        pose_stamped.pose.position.z = 0.0
        goal_msg.poses = [pose, pose_stamped]
        goal_msg.load = [2, -2]

        self._action_client.wait_for_server()

        self._action_client.send_goal_async(goal_msg)


def main(args=None):
    rclpy.init(args=args)

    action_client = FollowTargetActionClient()
    pose_stamped = PoseStamped()
    pose_stamped.pose.position.x = 3.62
    pose_stamped.pose.position.y = 0.42
    pose_stamped.pose.position.z = 0.0

    action_client.send_goal(pose_stamped)


if __name__ == '__main__':
    main()