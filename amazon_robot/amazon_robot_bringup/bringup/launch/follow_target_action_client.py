import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from amazon_robot_msg.action import FollowTargets
from geometry_msgs.msg import PoseStamped


pallets = {
    'pallet_0': {'x_pose': 3.62, 'y_pose': 0.42, 'z_pose': 0.01},
    'pallet_1': {'x_pose': 3.67, 'y_pose': -1.59, 'z_pose': 0.01},
    'pallet_2': {'x_pose': 3.67, 'y_pose': -3.98, 'z_pose': 0.01},
}
storage_locations = {
    'storage_location_1': {'x_pose': -5.10, 'y_pose': -3.98, 'z_pose': 0.01},
    'storage_location_2': {'x_pose': -5.14, 'y_pose': 0.45, 'z_pose': 0.01},
}

free_area = {
    'end_of_corridor': {'x_pose': 1.35, 'y_pose': -6.78, 'z_pose': 0.01},
}


lift_stages = { 'load': 2, 'unload': -2 , 'half_load': 1, 'half_unload': -1 , 'unchanged':0}


def get_pose_stamped(x_pose, y_pose, z_pose):
    pose_stamped = PoseStamped()
    pose_stamped.pose.position.x = x_pose
    pose_stamped.pose.position.y = y_pose
    pose_stamped.pose.position.z = z_pose
    return pose_stamped

class WarehouseController:

    def __init__(self):
        self.action_client1 = FollowTargetActionClient('/robot1/FollowTargets', 'robot1_follow_target_action_client')
        self.action_client2 = FollowTargetActionClient('/robot2/FollowTargets', 'robot2_follow_target_action_client')


    def send_plan(self):
        poses_robot1 = [get_pose_stamped(**pallets['pallet_0']), get_pose_stamped(**storage_locations['storage_location_1']) ]
        loads_robot1 = [lift_stages['load'], lift_stages['unload']]
        poses_robot2 = [get_pose_stamped(**free_area['end_of_corridor']), get_pose_stamped(**pallets['pallet_1']), get_pose_stamped(**storage_locations['storage_location_2']) ]
        loads_robot2 = [lift_stages['unchanged'], lift_stages['load'], lift_stages['unload']]
        #
        # print("Poses List ")
        # print(poses_robot1)
        # print("Load List ")
        # print(loads_robot1)
        print("Sending target goals to robot1 and robot2")

        self.action_client1.send_targets(poses_robot1, loads_robot1)
        self.action_client2.send_targets(poses_robot2, loads_robot2)


class FollowTargetActionClient(Node):

    def __init__(self, action_name = '/robot1/FollowTargets', action_client_name=  'follow_target_action_client'):
        super().__init__(action_client_name)
        self._action_client = ActionClient(self, FollowTargets, action_name)


    def send_targets(self, poses, loads):
        goal_msg = FollowTargets.Goal()
        goal_msg.poses = poses
        goal_msg.load = loads
        self._action_client.wait_for_server()
        self._action_client.send_goal_async(goal_msg)


def main(args=None):
    rclpy.init(args=args)
    warehouse_controller = WarehouseController()
    warehouse_controller.send_plan()

if __name__ == '__main__':
    main()