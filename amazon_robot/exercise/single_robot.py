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
    'pallet_1': {'x_pose': 3.64, 'y_pose': 0.63, 'z_pose': 0.01},
    'pallet_2': {'x_pose': 3.59, 'y_pose': -1.11, 'z_pose': 0.01},
    'pallet_3': {'x_pose': 3.51, 'y_pose': -2.84, 'z_pose': 0.01},
    'pallet_4': {'x_pose': 3.49, 'y_pose': -4.68, 'z_pose': 0.01},
    'pallet_5': {'x_pose': 3.64, 'y_pose': -6.91, 'z_pose': 0.01},
    'pallet_6': {'x_pose': 3.64, 'y_pose': -8.88, 'z_pose': 0.01},
}

storage_locations = {
    'storage_location_1': {'x_pose': -5.84, 'y_pose': -3.35, 'z_pose': 0.01},
    'storage_location_2': {'x_pose': -5.84, 'y_pose': 1.12, 'z_pose': 0.01},
    'storage_location_3': {'x_pose': -5.84, 'y_pose': -7.76, 'z_pose': 0.01},
}

free_area = {
    'right_end_of_corridor': {'x_pose': 1.35, 'y_pose': -6.78, 'z_pose': 0.01},
    'left_end_of_corridor': {'x_pose': 0.92, 'y_pose': 6.45, 'z_pose': 0.01},
}

lift_stages = {'load': 2, 'unload': -2, 'half_load': 1, 'half_unload': -1, 'unchanged': 0}


# Helper function to convert x,y,z pose to PoseStamped pose format.
def get_pose_stamped(x_pose, y_pose, z_pose):
    pose_stamped = PoseStamped()
    pose_stamped.pose.position.x = x_pose
    pose_stamped.pose.position.y = y_pose
    pose_stamped.pose.position.z = z_pose
    return pose_stamped


# Use the action client to send plan
class SendDrivingPlan:

    def __init__(self):
        # Action Client Definition
        self.action_client = FollowTargetActionClient('/FollowTargets', 'follow_target_action_client')

    # TODO: Use this function to create your plan
    def create_plan(self):
        pass

    def create_test_plan(self):
        poses_robot = [get_pose_stamped(**pallets['pallet_1']),
                       get_pose_stamped(**storage_locations['storage_location_1']),
                       # get_pose_stamped(**pallets['pallet_2']),
                       # get_pose_stamped(**storage_locations['storage_location_2'])
                       ]
        loads_robot = [
            lift_stages['load'],
            lift_stages['unload'],
            # lift_stages['load'],
            # lift_stages['unload']
        ]

        print("Sending target goals to the robot")
        self.action_client.send_targets(poses_robot, loads_robot)

    def execute_plan(self):
        None


# Write your action client here
class FollowTargetActionClient(Node):

    def __init__(self, action_name='/FollowTargets', action_client_name='follow_target_action_client'):
        super().__init__(action_client_name)
        self._action_client = ActionClient(self, FollowTargets, action_name)

    def get_action_client(self):
        return self._action_client

    def send_targets(self, poses, loads):
        self.get_logger().info('Received Goal poses: {0}'.format(len(poses)))
        self.get_logger().info('Received Load instructions: {0}'.format(len(loads)))
        if len(poses) == len(loads):
            goal_msg = FollowTargets.Goal()
            goal_msg.poses = poses
            goal_msg.load = loads
            self.goal_length = len(poses)
            self._action_client.wait_for_server()
            self._action_client.send_goal_async(goal_msg, feedback_callback=self.feedback_callback)
        else:
            self.get_logger().warn('Unequal amount of Poses and loads!')

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        # self.get_logger().info('Currently Executing: {0} out of {0} targets'.format(feedback.current_waypoint, self.goal_length))


def main(args=None):
    rclpy.init(args=args)
    planner = SendDrivingPlan()
    planner.create_test_plan()
    planner.execute_plan()


if __name__ == '__main__':
    main()
