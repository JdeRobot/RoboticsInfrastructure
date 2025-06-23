#! /usr/bin/env python3
import sys
import copy
import rospy
import moveit_commander
import moveit_msgs.msg
import geometry_msgs.msg
from math import pi
from std_msgs.msg import String
from moveit_commander.conversions import pose_to_list
from tf.transformations import euler_from_quaternion, quaternion_from_euler

# Inicializacion, objetos robot y escena, grupos MoveIt
moveit_commander.roscpp_initialize(sys.argv)
rospy.init_node("moving_irb120_robot", anonymous=True)
robot = moveit_commander.RobotCommander()
scene = moveit_commander.PlanningSceneInterface()
arm_group = moveit_commander.MoveGroupCommander("irb_120")
hand_group = moveit_commander.MoveGroupCommander("robotiq_85")

# Inicializacion, objetos robot y escena, grupos MoveIt
display_trajectory_publisher = rospy.Publisher(
    "/move_group/display_planned_path", moveit_msgs.msg.DisplayTrajectory, queue_size=20
)


# Inverse Kinematics (IK): mover TCP (brida) a una orientacion dada (Euler) y posicion x, y, z dada. Los angulos se convierten a cuaternios (mensaje de pose)


def move_pose_arm(roll, pitch, yaw, x, y, z):
    pose_goal = geometry_msgs.msg.Pose()
    quat = quaternion_from_euler(
        roll * (pi / 180), pitch * (pi / 180), yaw * (pi / 180)
    )
    pose_goal.orientation.x = quat[0]
    pose_goal.orientation.y = quat[1]
    pose_goal.orientation.z = quat[2]
    pose_goal.orientation.w = quat[3]
    pose_goal.position.x = x
    pose_goal.position.y = y
    pose_goal.position.z = z
    arm_group.set_pose_target(pose_goal)

    plan = arm_group.go(wait=True)

    arm_group.stop()  # To guarantee no residual movement
    arm_group.clear_pose_targets()


# Forward Kinematics (FK) para la herramienta


def move_joint_hand(gripper_finger1_joint):
    joint_goal = hand_group.get_current_joint_values()
    joint_goal[2] = gripper_finger1_joint  # Gripper master axis

    hand_group.go(joint_goal, wait=True)
    hand_group.stop()  # To guarantee no residual movement


if __name__ == "__main__":

    # Ejemplo de uso de IK (en loop)
    for i in range(2):
        rospy.loginfo("Moving arm to HOME point")
        move_pose_arm(0, 90, 0, 0.4, 0, 0.6)
        rospy.loginfo("Opening gripper")
        move_joint_hand(0)
        rospy.sleep(1)
        rospy.loginfo("Moving arm to point_1")
        move_pose_arm(45, 45, 45, 0.5, -0.25, 0.3)
        rospy.sleep(1)
        rospy.loginfo("Moving arm to point_2")
        move_pose_arm(0, -90, 90, 0.5, 0.25, 0.3)
        rospy.sleep(1)
        rospy.loginfo("Closing gripper to 0.4")
        move_joint_hand(0.4)
        rospy.sleep(1)
        rospy.loginfo("Moving arm to point_3")
        move_pose_arm(0, 0, 90, 0.2, 0, 0.8)
        rospy.loginfo("Opening gripper")
        move_joint_hand(0)
        rospy.sleep(1)
        rospy.loginfo("Moving arm to point_4")
        move_pose_arm(0, 0, 0, 0, -0.5, 0.4)
        rospy.loginfo("Closing gripper to 0.6")
        move_joint_hand(0.6)
        rospy.sleep(1)

    rospy.loginfo("All movements finished. Shutting down")
    moveit_commander.roscpp_shutdown()
