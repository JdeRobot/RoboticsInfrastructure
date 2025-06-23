#! /usr/bin/env python3

import rospy
import rospkg

import sys
import copy
import os
import numpy

from actionlib import SimpleActionClient, GoalStatus

from moveit_commander import RobotCommander,PlanningSceneInterface
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
#from moveit_python import *

from geometry_msgs.msg import Pose, PoseStamped, PoseArray, Quaternion
from moveit_msgs.msg import PickupAction, PickupGoal
from moveit_msgs.msg import PlaceAction, PlaceGoal
from moveit_msgs.msg import PlaceLocation
from moveit_msgs.msg import MoveItErrorCodes
#from moveit_simple_grasps.msg import GenerateGraspsAction, GenerateGraspsGoal, GraspGeneratorOptions

from gazebo_msgs.srv import (
    SpawnModel,
    DeleteModel,
)

# Diccionaro con codigos de error de MoveIt:
moveit_error_dict = {}
for name in MoveItErrorCodes.__dict__.keys():
    if not name[:1] == '_':
        code = MoveItErrorCodes.__dict__[name]
        moveit_error_dict[code] = name


class Pick_Place:
    def __init__ (self):
        self.object_name = "box"
        self.object_width = 0.05

        self.arm_group = "irb_120"
        self.gripper_group = "robotiq_85"

        self.arm = moveit_commander.MoveGroupCommander("irb_120")
        self.gripper = moveit_commander.MoveGroupCommander("robotiq_85")

        self.scene = PlanningSceneInterface()
        self.robot = RobotCommander()

        rospy.sleep(1.0)

        self.scene.remove_world_object(self.object_name)

        self.pose_object = self.add_object(self.object_name)

        rospy.sleep(1.0)
	
	# Posicion para el PICK
        self.pose_object.position.z += 0.16 # Posición vertical de la brida del robot, no del TCP de la herramienta!
        print(self.pose_object.position)

	# Posicion para el PLACE
        self.pose_place = Pose()
        self.pose_place.position.x = 0.5
        self.pose_place.position.y = 0.2
        self.pose_place.position.z = 0.01 # Security margin
        self.pose_place.orientation = Quaternion(*quaternion_from_euler(0.0, 0.0, 0.0))
	
	# Parametros para la retirada de la pinza tras coger
        self.approach_retreat_desired_dist = 0.2
        self.approach_retreat_min_dist = 0.1

        print("Starting pick and place")

	# Generacion del mensaje de grasp y ejecución del PICK con la posicion y tamaño del objeto
        grasps = self.generate_grasps(self.pose_object, self.object_width)
        self.arm.pick(self.object_name, grasps)

        rospy.loginfo('Pick up successfully')
        rospy.sleep(1)
        
        # Generacion del mensaje de grasp para el PLACE y ejecución del PLACE con el nombre y posición del objeto.
        place = self.generate_places(self.pose_place)
        self.arm.place(self.object_name, place)

        rospy.loginfo('Place successfully')
        self.move_joint_hand(0) # Abrimos la pinza
        rospy.sleep(1)
        # Detach en RVIZ
        self.arm.detach_object(self.object_name)

        rospy.loginfo("Moving arm to HOME point")	
        self.move_pose_arm(0,0.8,0,0.4,0,0.6)
        
        self.clean_scene()

    def clean_scene(self):
        self.scene.remove_world_object(self.object_name)

    def add_object(self, name):
        p = PoseStamped()
        p.header.frame_id = self.robot.get_planning_frame()
        p.header.stamp = rospy.Time.now()

        p.pose.position.x = 0.5
        p.pose.position.y = 0.0
        p.pose.position.z = 0.015

        q = quaternion_from_euler(0.0, 0.0, 0.0)
        p.pose.orientation = Quaternion(*q)
        size = (0.05,0.05,0.05)

        self.scene.add_box(name, p, size)

        return p.pose

    def move_pose_arm(self, roll,pitch,yaw,x,y,z):
        pose_goal = geometry_msgs.msg.Pose()
        quat = quaternion_from_euler(roll,pitch,yaw)
        pose_goal.orientation.x = quat[0]
        pose_goal.orientation.y = quat[1]
        pose_goal.orientation.z = quat[2]
        pose_goal.orientation.w = quat[3]
        pose_goal.position.x = x
        pose_goal.position.y = y
        pose_goal.position.z = z
        self.arm.set_pose_target(pose_goal)

        plan = self.arm.go(wait=True)

        self.arm.stop() # To guarantee no residual movement
        self.arm.clear_pose_targets()

        # Movimiento eje a eje de la herramienta
    def move_joint_hand(self,gripper_finger1_joint):
        joint_goal = self.gripper.get_current_joint_values()
        joint_goal[2] = gripper_finger1_joint # Gripper master axis

        self.gripper.go(joint_goal, wait=True)
        self.gripper.stop() # To guarantee no residual movement

    def generate_grasps(self, pose, width):
        grasps = []

        now = rospy.Time.now()
        # Permitimos usar diferentes ángulos para coger el objeto (siempre verticalmente)
        for angle in numpy.arange(0.0, numpy.deg2rad(360.0), numpy.deg2rad(90.0)):
            # Create place location:
            grasp = Grasp()

            grasp.grasp_pose.header.stamp = now
            grasp.grasp_pose.header.frame_id = self.robot.get_planning_frame()
            grasp.grasp_pose.pose = copy.deepcopy(pose)
            q = quaternion_from_euler(0.0, numpy.deg2rad(90.0), angle)
            grasp.grasp_pose.pose.orientation = Quaternion(*q)

            # Setting pre-grasp approach
            grasp.pre_grasp_approach.direction.header.stamp = now
            grasp.pre_grasp_approach.direction.header.frame_id = self.robot.get_planning_frame()
            grasp.pre_grasp_approach.direction.vector.z = -0.2
            grasp.pre_grasp_approach.min_distance = self.approach_retreat_min_dist
            grasp.pre_grasp_approach.desired_distance = self.approach_retreat_desired_dist

            # Setting post-grasp retreat
            grasp.post_grasp_retreat.direction.header.stamp = now
            grasp.post_grasp_retreat.direction.header.frame_id = self.robot.get_planning_frame()
            grasp.post_grasp_retreat.direction.vector.z = 0.2
            grasp.post_grasp_retreat.min_distance = self.approach_retreat_min_dist
            grasp.post_grasp_retreat.desired_distance = self.approach_retreat_desired_dist

            grasp.max_contact_force = 0 #<=0 to disable 

            grasp.pre_grasp_posture.joint_names.append("gripper_finger1_joint")
            traj = JointTrajectoryPoint()
            traj.positions.append(0)
            traj.time_from_start = rospy.Duration.from_sec(0.5)
            grasp.pre_grasp_posture.points.append(traj)

            grasp.grasp_posture.joint_names.append("gripper_finger1_joint")
            traj = JointTrajectoryPoint()
            traj.positions.append(0.55)
            #traj.effort.append(100)
            traj.time_from_start = rospy.Duration.from_sec(1.0)
            grasp.grasp_posture.points.append(traj)

            grasps.append(grasp)

        return grasps

    def generate_places(self, target):
        #places = []
        now = rospy.Time.now()
        # for angle in numpy.arange(0.0, numpy.deg2rad(360.0), numpy.deg2rad(30.0)):
            # Create place location:
        place = PlaceLocation()

        place.place_pose.header.stamp = now
        place.place_pose.header.frame_id = self.robot.get_planning_frame()

        # Set target position:
        place.place_pose.pose = copy.deepcopy(target)

        # Generate orientation (wrt Z axis):
        q = quaternion_from_euler(0.0, 0, 0.0)
        place.place_pose.pose.orientation = Quaternion(*q)

        # Generate pre place approach:
        place.pre_place_approach.desired_distance = self.approach_retreat_desired_dist
        place.pre_place_approach.min_distance = self.approach_retreat_min_dist

        place.pre_place_approach.direction.header.stamp = now
        place.pre_place_approach.direction.header.frame_id = self.robot.get_planning_frame()

        place.pre_place_approach.direction.vector.x =  0
        place.pre_place_approach.direction.vector.y =  0
        place.pre_place_approach.direction.vector.z = -0.2

        # Generate post place approach:
        place.post_place_retreat.direction.header.stamp = now
        place.post_place_retreat.direction.header.frame_id = self.robot.get_planning_frame()

        place.post_place_retreat.desired_distance = self.approach_retreat_desired_dist
        place.post_place_retreat.min_distance = self.approach_retreat_min_dist

        place.post_place_retreat.direction.vector.x = 0
        place.post_place_retreat.direction.vector.y = 0
        place.post_place_retreat.direction.vector.z = 0.2

        place.allowed_touch_objects.append(self.object_name)

        place.post_place_posture.joint_names.append("gripper_finger1_joint")
        traj = JointTrajectoryPoint()
        traj.positions.append(0)
        #traj.effort.append(0)
        traj.time_from_start = rospy.Duration.from_sec(1.0)
        place.post_place_posture.points.append(traj)

            # Add place:
            #places.append(place)

        return place

    def create_pickup_goal(self, group, target, grasps):
        goal = PickupGoal()

        goal.group_name = group
        goal.target_name = target

        goal.possible_grasps.extend(grasps)

        goal.allowed_touch_objects.append(target)

        goal.allowed_planning_time = 3.0

        goal.planning_options.planning_scene_diff.is_diff = True
        goal.planning_options.planning_scene_diff.robot_state.is_diff = True
        goal.planning_options.plan_only = False
        goal.planning_options.replan = True
        goal.planning_options.replan_attempts = 20

        return goal

    def create_place_goal(self, group, target, places):
        goal = PlaceGoal()

        goal.group_name = group
        goal.target_name = target

        goal.possible_grasps.extend(places)

        goal.allowed_planning_time = 3.0

        goal.planning_options.planning_scene_diff.is_diff = True
        goal.planning_options.planning_scene_diff.robot_state.is_diff = True
        goal.planning_options.plan_only = False
        goal.planning_options.replan = True
        goal.planning_options.replan_attempts = 20

        return goal

    def pickup(self, group, target, width):
        print("start grnerating grasps")
        grasps = self.generate_grasps(self.pose_object, width)
        print("start creating pickup goal")
        goal = self.create_pickup_goal(group, target, grasps)

        state = self.pickup_action.send_goal_and_wait(goal)
        if state != GoalStatus.SUCCEEDED:
            rospy.logerr('Pick up goal failed!: %s' % self.pickup_action.get_goal_status_text())
            return None

        result = self.pickup_action.get_result()

        # Check for error:
        err = result.error_code.val
        if err != MoveItErrorCodes.SUCCESS:
            rospy.logwarn('Group %s cannot pick up target %s!: %s' % (group, target, str(moveit_error_dict[err])))

            return False

        return True

    def place(self, group, target, place):
        places = self.generate_places(self.pose_object, width)
        goal = self.create_place_goal(group, target, places)

        state = self.place_action.send_goal_and_wait(goal)
        if state != GoalStatus.SUCCEEDED:
            rospy.logerr('Pick up goal failed!: %s' % self.place_action.get_goal_status_text())
            return None

        result = self.place_action.get_result()

        # Check for error:
        err = result.error_code.val
        if err != MoveItErrorCodes.SUCCESS:
            rospy.logwarn('Group %s cannot pick up target %s!: %s' % (group, target, str(moveit_error_dict[err])))

            return False

        return True

if __name__ == "__main__":
    roscpp_initialize(sys.argv)
    rospy.init_node('pick_and_place')

    p = Pick_Place()

    rospy.spin()
    roscpp_shutdown()
