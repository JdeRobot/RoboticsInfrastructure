#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import Pose, PoseStamped, Point, Quaternion
from moveit_msgs.msg import CollisionObject, PlanningScene, PlanningOptions, PositionIKRequest, Constraints, JointConstraint, OrientationConstraint
from moveit_msgs.action import MoveGroup, ExecuteTrajectory
from moveit_msgs.srv import GetCartesianPath
from moveit_msgs.msg import RobotState
from shape_msgs.msg import SolidPrimitive
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from control_msgs.action import FollowJointTrajectory
import math
import time
import copy
from threading import Thread

class PickAndPlaceNode(Node):
    def __init__(self):
        super().__init__('pick_and_place_node')
        
        # Action Clients
        self.move_group_client = ActionClient(self, MoveGroup, 'move_action')
        self.execute_trajectory_client = ActionClient(self, ExecuteTrajectory, 'execute_trajectory')
        self.gripper_client = ActionClient(self, FollowJointTrajectory, '/gripper_controller/follow_joint_trajectory')
        self.cartesian_path_client = self.create_client(GetCartesianPath, 'compute_cartesian_path')

        # Publishers
        self.collision_pub = self.create_publisher(CollisionObject, '/collision_object', 10)
        
        # Wait for servers
        self.get_logger().info('Waiting for MoveGroup action server...')
        self.move_group_client.wait_for_server()
        self.get_logger().info('Waiting for ExecuteTrajectory action server...')
        self.execute_trajectory_client.wait_for_server()
        self.get_logger().info('Waiting for Cartesian Path service...')
        self.cartesian_path_client.wait_for_service()
        self.get_logger().info('Waiting for Gripper action server...')
        self.gripper_client.wait_for_server()
        
        self.get_logger().info('Servers up. Initializing scene...')
        
        # NOTE: Robot base_link is at world Z=0.9
        # All Z coordinates in base_link frame are relative to this
        
        # Add Conveyor Collision Object (at world Z=0.95, relative to base_link Z=0.05)
        self.add_collision_object(
            id='conveyor',
            shape_type=SolidPrimitive.BOX,
            dimensions=[2.4, 0.8, 0.1], 
            pose=Pose(position=Point(x=0.6, y=0.0, z=0.05), orientation=Quaternion(w=0.707, x=0.0, y=0.0, z=0.707)),
            frame_id='base_link'
        )
        
        # Add Table Collision Object (at world Z=0.73, relative to base_link Z=-0.17)
        self.add_collision_object(
            id='table',
            shape_type=SolidPrimitive.BOX,
            dimensions=[0.8, 1.6, 0.06],
            pose=Pose(position=Point(x=-0.6, y=0.0, z=-0.17), orientation=Quaternion(w=0.707, x=0.0, y=0.0, z=0.707)),
            frame_id='base_link'
        )
        
        # Add Bins (at world Z=0.755, relative to base_link Z=-0.145)
        bin_z = -0.145
        bins = [
            ('yellow_bin', -0.4, -0.45),
            ('red_bin', -0.4, 0.15),
            ('blue_bin', -0.4, 0.45),
            ('green_bin', -0.4, -0.15)
        ]
        
        for name, x, y in bins:
             self.add_collision_object(
                id=name,
                shape_type=SolidPrimitive.BOX,
                dimensions=[0.3, 0.3, 0.1],
                pose=Pose(position=Point(x=x, y=y, z=bin_z), orientation=Quaternion(w=1.0, x=0.0, y=0.0, z=0.0)),
                frame_id='base_link'
            )

        # Define Pick and Place Tasks
        # Objects are at world Z: 1.04-1.07
        # In base_link frame (base at world Z=0.9): objects at Z=0.14-0.17
        gripper_offset = 0.125  # Slightly deeper grasp (was 0.13)
        
        # Adjusted widths for better grasping
        self.tasks = [
            {'name': 'Red Box', 'id': 'red_box', 'width': 0.055, 'pick': [0.6, -0.3, 0.14 + gripper_offset], 'drop': [-0.4, 0.15, 0.0]},
            # {'name': 'Yellow Box', 'id': 'yellow_box', 'width': 0.045, 'pick': [0.6, 0.3, 0.15 + gripper_offset], 'drop': [-0.4, -0.45, 0.0]},
            # {'name': 'Blue Ball', 'id': 'blue_ball', 'width': 0.085, 'pick': [0.7, 0.1, 0.14 + gripper_offset], 'drop': [-0.4, 0.45, 0.0]},
            # {'name': 'Green Cylinder', 'id': 'green_cylinder', 'width': 0.065, 'pick': [0.5, -0.1, 0.17 + gripper_offset], 'drop': [-0.4, -0.15, 0.0]}
        ]
        
        # Orientation for picking (Pointing down)
        self.down_orientation = Quaternion(x=1.0, y=0.0, z=0.0, w=0.0) 
        
        self.routine_started = False
        
        # Start routine in a separate thread to avoid blocking
        time.sleep(2.0)  # Wait for everything to initialize
        thread = Thread(target=self.execute_routine_thread)
        thread.daemon = True
        thread.start()

    def add_collision_object(self, id, shape_type, dimensions, pose, frame_id):
        co = CollisionObject()
        co.header.frame_id = frame_id
        co.id = id
        co.operation = CollisionObject.ADD
        
        primitive = SolidPrimitive()
        primitive.type = shape_type
        primitive.dimensions = dimensions
        co.primitives.append(primitive)
        co.primitive_poses.append(pose)
        
        self.collision_pub.publish(co)

    def remove_collision_object(self, id):
        co = CollisionObject()
        co.id = id
        co.operation = CollisionObject.REMOVE
        self.collision_pub.publish(co)

    def calculate_gripper_value(self, width):
        """
        Calculate gripper position based on object width
        0.0 rad = 0.085m (Open)
        0.8 rad = 0.0m (Closed)
        """
        # Clamp width to valid range
        if width > 0.085: 
            width = 0.085
        if width < 0.0:
            width = 0.0
        
        # Calculate base position
        val = 0.8 * (1.0 - (width / 0.085))
        
        # Add squeeze factor to ensure firm grip
        squeeze_factor = 0.2  # Increased for stronger grip
        val += squeeze_factor
        
        # Clamp to valid range
        if val > 0.8: 
            val = 0.8
        if val < 0.0:
            val = 0.0
            
        return val

    def execute_routine_thread(self):
        """Execute routine in a separate thread"""
        if self.routine_started:
            return
        self.routine_started = True
        
        self.get_logger().info('Starting Pick and Place Routine...')
        self.get_logger().info('Robot base_link is at world Z=0.9')
        self.get_logger().info('Objects are at world Z=1.04-1.07 (base_link Z=0.14-0.17)')
        
        # Open Gripper first (0.0 = fully open)
        self.get_logger().info('Opening gripper to start...')
        self.control_gripper(position=0.0)
        time.sleep(2.0)  # Wait for gripper to fully open
        
        # Define a safe home pose (high up)
        home_pose = [0.0, -0.4, 0.4] # X, Y, Z relative to base
        
        for task in self.tasks:
            self.get_logger().info(f"\n{'='*50}")
            self.get_logger().info(f"Processing: {task['name']}")
            self.get_logger().info(f"{'='*50}")
            
            # 0. Move to Home/Safe position first
            self.get_logger().info(f"Step 0: Moving to safe home position")
            success = self.move_arm_to_pose(home_pose, self.down_orientation)
            if not success:
                self.get_logger().warn("Failed to reach home position, continuing...")
            
            time.sleep(1.0)

            # 1. Move to Pre-Pick (Above object)
            pick_pose = task['pick']
            pre_pick_pose = copy.deepcopy(pick_pose)
            pre_pick_pose[2] += 0.10  # 10cm above pick height
            
            self.get_logger().info(f"Step 1: Moving to pre-pick position above {task['name']}")
            success = self.move_arm_to_pose(pre_pick_pose, self.down_orientation)
            if not success:
                self.get_logger().error(f"Failed to move to pre-pick for {task['name']}")
                continue
            
            time.sleep(2.0)
                
            # 2. Move to Pick (Down to object)
            self.get_logger().info(f"Step 2: Moving down to pick position (Cartesian)")
            success = self.move_cartesian(pick_pose)
            if not success: 
                self.get_logger().error(f"Failed to reach pick position for {task['name']}")
                continue
            
            time.sleep(2.0)
            
            # 3. Close Gripper to grasp object
            target_width = task['width']
            target_pos = self.calculate_gripper_value(target_width)
            self.get_logger().info(f"Step 3: Closing gripper to {target_pos:.3f} rad for object width {target_width}m")
            self.control_gripper(position=target_pos)
            time.sleep(4.0)  # Longer wait for physics to settle and grip to establish
            
            # 4. Move to Post-Pick (Lift up with object)
            self.get_logger().info(f"Step 4: Lifting object up (Cartesian)")
            success = self.move_cartesian(pre_pick_pose)
            if not success: 
                self.get_logger().error(f"Failed to lift {task['name']}")
                continue
            
            time.sleep(2.0)
            
            # 4.5 Move to Safe Home Position (With object)
            self.get_logger().info(f"Step 4.5: Moving to safe home position with object")
            success = self.move_arm_to_pose(home_pose, self.down_orientation)
            if not success:
                self.get_logger().error("Failed to reach home position with object")
                continue

            time.sleep(1.0)
            
            # 5. Move to Pre-Drop Location (Above Bin)
            drop_pose = task['drop']
            pre_drop_pose = copy.deepcopy(drop_pose)
            pre_drop_pose[2] += 0.25  # High above bin

            self.get_logger().info(f"Step 5: Moving to pre-drop location")
            success = self.move_arm_to_pose(pre_drop_pose, self.down_orientation)
            if not success: 
                self.get_logger().error(f"Failed to move to pre-drop location for {task['name']}")
                continue
            
            time.sleep(1.0)

            # Identify bin name for collision removal
            bin_name = task['id'].replace('_box', '_bin')
            self.remove_collision_object(bin_name)
            time.sleep(0.5) # Wait for scene update

            # Try to lower to drop location
            self.get_logger().info(f"Step 5b: Lowering to drop location")
            at_low_drop = False
            if self.move_cartesian(drop_pose):
                at_low_drop = True
            else:
                self.get_logger().warn("Could not reach low drop height, dropping from pre-drop height (Fallback)")
            
            # 6. Open Gripper to release object
            self.get_logger().info(f"Step 6: Opening gripper to release object")
            self.control_gripper(position=0.0)
            time.sleep(2.0)  # Wait for gripper to fully open and object to drop
            
            # Return to pre-drop if we went down
            if at_low_drop:
                self.get_logger().info(f"Step 7: Returning to pre-drop height")
                self.move_cartesian(pre_drop_pose)
            
            self.get_logger().info(f"✓ Successfully completed {task['name']}\n")
            
        self.get_logger().info('='*50)
        self.get_logger().info('Pick and Place Routine Completed!')
        self.get_logger().info('='*50)
        
    def move_cartesian(self, target_pose, steps=10):
        """
        Move in a straight line to target_pose using Cartesian path planning.
        """
        req = GetCartesianPath.Request()
        req.header.frame_id = 'base_link'
        req.header.stamp = self.get_clock().now().to_msg()
        req.group_name = 'ur5_manipulator'
        
        # Define waypoints (Start is implicit current state, End is target)
        # We can add intermediate points if needed, but 1 point is usually enough for a straight line
        req.waypoints = [Pose(position=Point(x=target_pose[0], y=target_pose[1], z=target_pose[2]), 
                              orientation=self.down_orientation)]
        
        req.max_step = 0.01  # 1cm resolution
        req.jump_threshold = 0.0  # Disable jump check (or set >0 to detect big jumps)
        req.avoid_collisions = True
        
        # Call service
        self.get_logger().info(f"  → Computing Cartesian path to: {target_pose}")
        future = self.cartesian_path_client.call_async(req)
        
        # Wait for future to complete (since node is spinning in main thread)
        while not future.done():
            time.sleep(0.05)
            
        response = future.result()
        
        if not response or response.error_code.val != 1:
            self.get_logger().error(f"  ✗ Cartesian path computation failed (Error: {response.error_code.val if response else 'None'})")
            return False
            
        if response.fraction < 0.9:
            self.get_logger().error(f"  ✗ Cartesian path incomplete (Fraction: {response.fraction})")
            return False
            
        # Execute Trajectory
        self.get_logger().info(f"  → Path computed (Fraction: {response.fraction:.2f}). Executing...")
        
        goal = ExecuteTrajectory.Goal()
        goal.trajectory = response.solution
        
        send_goal_future = self.execute_trajectory_client.send_goal_async(goal)
        
        while not send_goal_future.done():
            time.sleep(0.05)
            
        goal_handle = send_goal_future.result()
        
        if not goal_handle.accepted:
            self.get_logger().error('  ✗ Cartesian execution rejected')
            return False
            
        result_future = goal_handle.get_result_async()
        
        while not result_future.done():
            time.sleep(0.05)
            
        result = result_future.result()
        
        if result.result.error_code.val == 1:
            self.get_logger().info('  ✓ Cartesian move successful')
            return True
        else:
            self.get_logger().error(f"  ✗ Cartesian execution failed (Error: {result.result.error_code.val})")
            return False

    def move_arm_to_pose(self, position, orientation):
        goal_msg = MoveGroup.Goal()
        goal_msg.request.workspace_parameters.header.frame_id = 'base_link'
        goal_msg.request.workspace_parameters.min_corner.x = -1.0
        goal_msg.request.workspace_parameters.min_corner.y = -1.0
        goal_msg.request.workspace_parameters.min_corner.z = -1.0
        goal_msg.request.workspace_parameters.max_corner.x = 1.0
        goal_msg.request.workspace_parameters.max_corner.y = 1.0
        goal_msg.request.workspace_parameters.max_corner.z = 1.0
        
        goal_msg.request.start_state.is_diff = True
        goal_msg.request.group_name = 'ur5_manipulator'
        goal_msg.request.allowed_planning_time = 20.0
        goal_msg.request.num_planning_attempts = 10  # Try harder to find a valid plan
        goal_msg.request.max_velocity_scaling_factor = 0.2  # Increased for better reachability
        goal_msg.request.max_acceleration_scaling_factor = 0.2

        
        # Constraints
        from moveit_msgs.msg import PositionConstraint, BoundingVolume
        pc = PositionConstraint()
        pc.header.frame_id = 'base_link'
        pc.link_name = 'tool0'
        pc.target_point_offset.x = 0.0
        pc.target_point_offset.y = 0.0
        pc.target_point_offset.z = 0.0
        
        bv = BoundingVolume()
        sp = SolidPrimitive()
        sp.type = SolidPrimitive.SPHERE
        sp.dimensions = [0.02]  # 2cm tolerance
        bv.primitives.append(sp)
        bv.primitive_poses.append(Pose(position=Point(x=position[0], y=position[1], z=position[2])))
        
        pc.constraint_region = bv
        pc.weight = 1.0
        
        # Orientation Constraint
        oc_goal = OrientationConstraint()
        oc_goal.header.frame_id = 'base_link'
        oc_goal.link_name = 'tool0'
        oc_goal.orientation = orientation
        oc_goal.absolute_x_axis_tolerance = 0.5  # Relaxed to prevent self-collisions (was 0.2)
        oc_goal.absolute_y_axis_tolerance = 0.5
        oc_goal.absolute_z_axis_tolerance = 0.5
        oc_goal.weight = 1.0
        
        goal_msg.request.goal_constraints.append(Constraints(
            position_constraints=[pc],
            orientation_constraints=[oc_goal]
        ))
        
        goal_msg.planning_options.plan_only = False
        
        self.get_logger().info(f"  → Target position: [{position[0]:.3f}, {position[1]:.3f}, {position[2]:.3f}]")
        
        # Send goal and wait for result
        send_goal_future = self.move_group_client.send_goal_async(goal_msg)
        
        # Wait for goal to be accepted
        while not send_goal_future.done():
            time.sleep(0.05)
        
        goal_handle = send_goal_future.result()
        
        if not goal_handle:
            self.get_logger().error('  ✗ Goal was not accepted (timeout or failure)')
            return False

        if not goal_handle.accepted:
            self.get_logger().error('  ✗ Goal rejected by MoveGroup')
            return False
        
        self.get_logger().info('  → Goal accepted, waiting for result...')
        
        # Wait for result
        result_future = goal_handle.get_result_async()
        
        while not result_future.done():
            time.sleep(0.05)
        
        result = result_future.result()
        
        if result is None:
            self.get_logger().error('  ✗ Timeout waiting for result')
            return False
        
        if result.result.error_code.val == 1:  # SUCCESS
            self.get_logger().info('  ✓ Movement successful')
            return True
        else:
            self.get_logger().error(f"  ✗ MoveGroup failed with error code: {result.result.error_code.val}")
            return False

    def control_gripper(self, position):
        """
        Control gripper position
        position: 0.0 = fully open (0.085m), 0.8 = fully closed (0.0m)
        """
        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = ['robotiq_85_left_knuckle_joint']
        
        point = JointTrajectoryPoint()
        point.positions = [position]
        point.time_from_start.sec = 2  # Give 2 seconds to reach position
        
        goal.trajectory.points.append(point)
        
        self.get_logger().info(f"  → Sending gripper command: {position:.3f} rad")
        
        # Send goal and wait
        send_goal_future = self.gripper_client.send_goal_async(goal)
        
        while not send_goal_future.done():
            time.sleep(0.05)
        
        goal_handle = send_goal_future.result()
        
        if not goal_handle:
            self.get_logger().error('  ✗ Gripper goal not accepted (timeout or failure)')
            return

        if not goal_handle.accepted:
            self.get_logger().error('  ✗ Gripper goal rejected')
            return
        
        self.get_logger().info("  → Waiting for gripper to complete movement...")
        
        # Wait for result
        result_future = goal_handle.get_result_async()
        
        while not result_future.done():
            time.sleep(0.05)
        
        result = result_future.result()
        
        if result is None:
            self.get_logger().warn('  ⚠ Gripper timeout, continuing anyway')
            return
        
        if result.result.error_code == 0:  # SUCCESS
            self.get_logger().info(f"  ✓ Gripper reached position {position:.3f} rad")
        else:
            self.get_logger().warn(f"  ⚠ Gripper action finished with error code: {result.result.error_code}")

from rclpy.executors import MultiThreadedExecutor

def main(args=None):
    rclpy.init(args=args)
    node = PickAndPlaceNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()