#! /usr/bin/env python

import rospy
import rospkg

import sys
import copy
import os
import numpy

from moveit_commander import RobotCommander, PlanningSceneInterface
from moveit_commander import roscpp_initialize, roscpp_shutdown
from moveit_commander.conversions import pose_to_list
import moveit_commander
import moveit_msgs.msg
import geometry_msgs.msg
from moveit_msgs.msg import Grasp, PlaceLocation
from trajectory_msgs.msg import JointTrajectoryPoint
from std_msgs.msg import String

from math import pi
from tf.transformations import euler_from_quaternion, quaternion_from_euler

from geometry_msgs.msg import Pose, PoseStamped, PoseArray, Quaternion


class Object:
    def __init__(self, pose, height, width, shape, color):
        self.pose = pose
        self.height = height
        self.width = width
        self.shape = shape
        self.color = color


class Pick_Place:
    def __init__(self):
        self.object_list = {}

        self.arm = moveit_commander.MoveGroupCommander("irb_120")
        self.gripper = moveit_commander.MoveGroupCommander("robotiq_85")

        self.arm.set_goal_tolerance(0.05)
        self.gripper.set_goal_tolerance(0.02)

        self.scene = PlanningSceneInterface()
        self.robot = RobotCommander()
        rospy.sleep(1)

        self.add_objects()
        self.add_table()
        # self.add_ground()

        self.approach_retreat_desired_dist = 0.2
        self.approach_retreat_min_dist = 0.1

        rospy.sleep(1.0)

    # pick up object in pose
    def pickup(self, object_name, pose):
        grasps = self.generate_grasps(object_name, pose)
        self.arm.pick(object_name, grasps)
        # self.gripper.stop()

        rospy.loginfo("Pick up successfully")
        self.arm.detach_object(object_name)
        self.clean_scene(object_name)
        # rospy.sleep(1)

    # place object to goal pose
    def place(self, pose):
        self.move_pose_arm(pose)
        rospy.sleep(1)

        # pose.position.z -= 0.1
        # self.move_pose_arm(pose)

        waypoints = []
        wpose = self.arm.get_current_pose().pose
        wpose.position.z -= 0.15
        waypoints.append(copy.deepcopy(wpose))

        (plan, fraction) = self.arm.compute_cartesian_path(
            waypoints, 0.01, 0.0  # waypoints to follow  # eef_step
        )  # jump_threshold
        self.arm.execute(plan, wait=True)

        self.move_joint_hand(0)
        rospy.sleep(1)

        # pose.position.z += 0.1
        # self.move_pose_arm(pose)

        waypoints = []
        wpose = self.arm.get_current_pose().pose
        wpose.position.z += 0.15
        waypoints.append(copy.deepcopy(wpose))

        (plan, fraction) = self.arm.compute_cartesian_path(
            waypoints, 0.01, 0.0  # waypoints to follow  # eef_step
        )  # jump_threshold
        self.arm.execute(plan, wait=True)

        rospy.loginfo("Place successfully")

    def get_object_pose(self, object_name):
        pose = self.object_list[object_name].pose
        return pose

    def clean_scene(self, object_name):
        self.scene.remove_world_object(object_name)

    def add_ground(self):
        self.clean_scene("ground")

        p = PoseStamped()
        p.header.frame_id = self.robot.get_planning_frame()
        p.header.stamp = rospy.Time.now()
        p.pose.position.x = 0.0
        p.pose.position.y = 0.0
        p.pose.position.z = -0.01
        size = (5, 5, 0.02)

        # self.scene.add_box("ground",p, size)
        rospy.sleep(2)

    def add_table(self):
        self.clean_scene("table")

        p = PoseStamped()
        p.header.frame_id = self.robot.get_planning_frame()
        p.header.stamp = rospy.Time.now()
        p.pose.position.x = 0.8
        p.pose.position.y = 0.0
        p.pose.position.z = 0.1
        size = (0.8, 1.5, 0.028)

        self.scene.add_box("table", p, size)
        rospy.sleep(2)

    def add_objects(self):
        p = PoseStamped()
        p.header.frame_id = self.robot.get_planning_frame()
        p.header.stamp = rospy.Time.now()

        # add box
        name = "box"
        self.clean_scene(name)
        p.pose.position.x = 0.5
        p.pose.position.y = 0.0
        p.pose.position.z = 0.025 + 0.115

        q = quaternion_from_euler(0.0, 0.0, 0.0)
        p.pose.orientation = Quaternion(*q)
        size = (0.05, 0.05, 0.05)

        self.scene.add_box(name, p, size)

        height = 0.05
        width = 0.05
        shape = "cube"
        color = "red"
        self.object_list[name] = Object(p.pose, height, width, shape, color)
        print("add box")
        rospy.sleep(1)

        p = PoseStamped()
        p.header.frame_id = self.robot.get_planning_frame()
        p.header.stamp = rospy.Time.now()

        # add cylinder
        name = "cylinder"
        self.clean_scene(name)
        p.pose.position.x = 0.5
        p.pose.position.y = 0.2
        p.pose.position.z = 0.05 + 0.115

        q = quaternion_from_euler(0.0, 0.0, 0.0)
        p.pose.orientation = Quaternion(*q)

        height = 0.1
        radius = 0.03

        self.scene.add_cylinder(name, p, height, radius)

        height = 0.1
        width = 0.03
        shape = "cylinder"
        color = "green"
        self.object_list[name] = Object(p.pose, height, width, shape, color)
        print("add cylinder")
        rospy.sleep(1)

        p = PoseStamped()
        p.header.frame_id = self.robot.get_planning_frame()
        p.header.stamp = rospy.Time.now()

        # add sphere
        name = "ball"
        self.clean_scene(name)
        p.pose.position.x = 0.5
        p.pose.position.y = -0.2
        p.pose.position.z = 0.03 + 0.115

        q = quaternion_from_euler(0.0, 0.0, 0.0)
        p.pose.orientation = Quaternion(*q)

        radius = 0.03

        self.scene.add_sphere(name, p, radius)

        height = 0.03
        width = 0.03
        shape = "sphere"
        color = "red"
        self.object_list[name] = Object(p.pose, height, width, shape, color)
        print("add ball")
        rospy.sleep(1)

        # print(self.object_list)

    def pose2msg(self, roll, pitch, yaw, x, y, z):
        pose = geometry_msgs.msg.Pose()
        quat = quaternion_from_euler(roll, pitch, yaw)
        pose.orientation.x = quat[0]
        pose.orientation.y = quat[1]
        pose.orientation.z = quat[2]
        pose.orientation.w = quat[3]
        pose.position.x = x
        pose.position.y = y
        pose.position.z = z

        return pose

    def msg2pose(self, pose):
        x = pose.position.x
        y = pose.position.y
        z = pose.position.z
        quaternion = (
            pose.orientation.x,
            pose.orientation.y,
            pose.orientation.z,
            pose.orientation.w,
        )
        euler = euler_from_quaternion(quaternion)
        roll = euler[0]
        pitch = euler[1]
        yaw = euler[2]

        return roll, pitch, yaw, x, y, z

    def back_to_home(self):
        self.move_joint_arm(0, 0, 0, 0, 0, 0)
        self.move_joint_hand(0)
        rospy.sleep(1)

    # Forward Kinematics (FK): move the arm by axis values
    def move_joint_arm(self, joint_0, joint_1, joint_2, joint_3, joint_4, joint_5):
        joint_goal = self.arm.get_current_joint_values()
        joint_goal[0] = joint_0
        joint_goal[1] = joint_1
        joint_goal[2] = joint_2
        joint_goal[3] = joint_3
        joint_goal[4] = joint_4
        joint_goal[5] = joint_5

        self.arm.go(joint_goal, wait=True)
        self.arm.stop()  # To guarantee no residual movement

    # Inverse Kinematics: Move the robot arm to desired pose
    def move_pose_arm(self, pose_goal):
        self.arm.set_pose_target(pose_goal)

        self.arm.go(wait=True)

        self.arm.stop()  # To guarantee no residual movement
        self.arm.clear_pose_targets()

    # Move the Robotiq gripper by master axis
    def move_joint_hand(self, gripper_finger1_joint):
        joint_goal = self.gripper.get_current_joint_values()
        joint_goal[2] = gripper_finger1_joint  # Gripper master axis

        self.gripper.go(joint_goal, wait=True)
        self.gripper.stop()  # To guarantee no residual movement

    def generate_grasps(self, name, pose):
        grasps = []

        now = rospy.Time.now()
        angle = 0
        grasp = Grasp()

        grasp.grasp_pose.header.stamp = now
        grasp.grasp_pose.header.frame_id = self.robot.get_planning_frame()
        grasp.grasp_pose.pose = copy.deepcopy(pose)

        # Setting pre-grasp approach
        grasp.pre_grasp_approach.direction.header.stamp = now
        grasp.pre_grasp_approach.direction.header.frame_id = (
            self.robot.get_planning_frame()
        )
        grasp.pre_grasp_approach.direction.vector.z = -0.5
        grasp.pre_grasp_approach.min_distance = self.approach_retreat_min_dist
        grasp.pre_grasp_approach.desired_distance = self.approach_retreat_desired_dist

        # Setting post-grasp retreat
        grasp.post_grasp_retreat.direction.header.stamp = now
        grasp.post_grasp_retreat.direction.header.frame_id = (
            self.robot.get_planning_frame()
        )
        grasp.post_grasp_retreat.direction.vector.z = 0.5
        grasp.post_grasp_retreat.min_distance = self.approach_retreat_min_dist
        grasp.post_grasp_retreat.desired_distance = self.approach_retreat_desired_dist

        q = quaternion_from_euler(0.0, numpy.deg2rad(90.0), angle)
        grasp.grasp_pose.pose.orientation = Quaternion(*q)

        grasp.max_contact_force = 1000

        grasp.pre_grasp_posture.joint_names.append("gripper_finger1_joint")
        traj = JointTrajectoryPoint()
        traj.positions.append(0.0)
        traj.time_from_start = rospy.Duration.from_sec(0.5)
        grasp.pre_grasp_posture.points.append(traj)

        grasp.grasp_posture.joint_names.append("gripper_finger1_joint")
        traj = JointTrajectoryPoint()
        if name == "box":
            traj.positions.append(0.4)
        elif name == "ball":
            traj.positions.append(0.3)
        elif name == "cylinder":
            traj.positions.append(0.3)

        # traj.velocities.append(0.2)
        # traj.effort.append(100)
        traj.time_from_start = rospy.Duration.from_sec(5.0)
        grasp.grasp_posture.points.append(traj)

        grasps.append(grasp)

        return grasps

    # Implement the main algorithm here
    def MyAlgorithm(self):
        self.back_to_home()

        # pick cylinder
        object_name = "cylinder"
        pose = self.get_object_pose(object_name)
        print(pose.position.y)
        pose.position.z += 0.16
        self.pickup(object_name, pose)

        roll = 0.0
        pitch = numpy.deg2rad(90.0)
        yaw = 0.0
        x = 0
        y = 0.6
        z = pose.position.z + 0.01
        place_pose = self.pose2msg(roll, pitch, yaw, x, y, z)
        self.place(place_pose)

        self.back_to_home()

        # pick box
        object_name = "box"
        pose = self.get_object_pose(object_name)
        print(pose.position.y)
        pose.position.z += 0.15
        self.pickup(object_name, pose)

        roll = 0.0
        pitch = numpy.deg2rad(90.0)
        yaw = 0.0
        x = 0.1
        y = 0.6
        z = pose.position.z + 0.01
        place_pose = self.pose2msg(roll, pitch, yaw, x, y, z)
        self.place(place_pose)

        self.back_to_home()

        # pick ball
        object_name = "ball"
        pose = self.get_object_pose(object_name)
        print(pose.position.y)
        pose.position.z += 0.14
        self.pickup(object_name, pose)

        roll = 0.0
        pitch = numpy.deg2rad(90.0)
        yaw = 0.0
        x = -0.1
        y = 0.6
        z = pose.position.z + 0.01
        place_pose = self.pose2msg(roll, pitch, yaw, x, y, z)
        self.place(place_pose)

        self.back_to_home()


if __name__ == "__main__":
    roscpp_initialize(sys.argv)
    rospy.init_node("pick_and_place")

    p = Pick_Place()
    p.MyAlgorithm()

    rospy.spin()
    roscpp_shutdown()
