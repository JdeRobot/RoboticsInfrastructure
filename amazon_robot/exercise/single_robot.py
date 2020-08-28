import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from amazon_robot_msg.action import FollowTargets
from geometry_msgs.msg import PoseStamped

'''
The end goal of this exercise is to have our robot autonomously drive around and perform series
of load-unload tasks to move pallets around. But before trying to implement this, you will have to
understand ROS2 architecture, how navigation 2 stack works, what are behaviour trees (BT) and ROS action client.

Overall, this exercise might provide you with a starting point to get into development
using ROS 2 and navigation 2. Additionally, you can also use the exercise for researching 
in different navigation components such as path planners and costmaps.

Following are some of the mandatory (!) , optional (/) and feature(*) goals. 
Feature goals require adding some functionality in the existing framework,
which you will also have to implement by yourself.

1. (!) Driving robot around autonomously with a pre-determined drive plan or waypoints.
2. (!) Correctly loading and unloading pallets at the waypoints and successfully moving them to another location
3. (!) Using ROS2 action client to publish a feedback of current waypoint.
4. (!) Modifying behaviour trees (BT) to implement *"Wait"* behaviour.
5. (/) Using different path planner and observing its effects
6. (/) Using different costmap
7. (/) Modifying behaviour trees to implement complex behaviours such as No-Go Zone.
8. (*) Implementing new BT plugins for approach behaviour ( When close to the pallet). 
9. (*) Implementing charging concept by creating new costmap plugin.
10. (*) Implementing different path planners and comparing them in a warehouse environment. 

and so on ..


You can consider following parameters while making the plan:
1. Distance from robot to the nearest pallet
2. Distance of pallet from the storage location
3. Current waypoints, remaining waypoints ..
4. State of the lift joint  

To access these parameters, you will have to use various ros concepts such as subscribing to a topic or 
creating an action client (just like this one!)

For example, to get a path between current position of the robot and another position (in our case, a pallet
at positon (x,y,z)), you can call the action server /compute_path_to_pose which will return you 
an array of points of the path.

You can also get the current robot position using robot odometry topic (/odom), which you can use for
different calculations. You can also experiment with different path planners, costmaps, behaviour trees and planners.


Following topics might be helpful:
/amcl_pose
/scan
/imu
/odom
/initialpose
/cmd_vel
/map


Following action servers might be useful:
/FollowTargets
/backup
/compute_path_to_pose
/follow_path
/navigate_to_pose
/spin
/wait


Have fun!

'''

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

lift_stages = {'load': 2, 'unload': -2, 'half_load': 1, 'half_unload': -1, 'unchanged': 0}


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

    # TODO: Use this function to create your plan
    def create_plan(self):
        pass

    def create_test_plan(self):
        poses_robot1 = [get_pose_stamped(**pallets['pallet_0']),
                        get_pose_stamped(**storage_locations['storage_location_1'])]
        loads_robot1 = [lift_stages['load'], lift_stages['unload']]
        poses_robot2 = [get_pose_stamped(**free_area['end_of_corridor']), get_pose_stamped(**pallets['pallet_1']),
                        get_pose_stamped(**storage_locations['storage_location_2'])]
        loads_robot2 = [lift_stages['unchanged'], lift_stages['load'], lift_stages['unload']]
        #
        # print("Poses List ")
        # print(poses_robot1)
        # print("Load List ")
        # print(loads_robot1)
        print("Sending target goals to robot1 and robot2")

        self.action_client1.send_targets(poses_robot1, loads_robot1)
        self.action_client2.send_targets(poses_robot2, loads_robot2)

    def execute_plan(self):
        rclpy.spin(self.action_client1)
        rclpy.spin(self.action_client2)


class FollowTargetActionClient(Node):

    def __init__(self, action_name='/robot1/FollowTargets', action_client_name='follow_target_action_client'):
        super().__init__(action_client_name)
        self._action_client = ActionClient(self, FollowTargets, action_name)

    def get_action_client(self):
        return self._action_client

    def send_targets(self, poses, loads):
        goal_msg = FollowTargets.Goal()
        goal_msg.poses = poses
        goal_msg.load = loads
        self._action_client.wait_for_server()
        self._action_client.send_goal_async(goal_msg, feedback_callback=self.feedback_callback)

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        print(feedback)
        # self.get_logger().info('Received feedback: {0}'.format(feedback.partial_sequence))


def main(args=None):
    rclpy.init(args=args)
    warehouse_controller = WarehouseController()
    warehouse_controller.create_test_plan()
    warehouse_controller.execute_plan()


if __name__ == '__main__':
    main()
