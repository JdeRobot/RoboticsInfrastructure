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
rospy.init_node('moving_irb120_robot', anonymous=True)
robot = moveit_commander.RobotCommander()
scene = moveit_commander.PlanningSceneInterface()
arm_group = moveit_commander.MoveGroupCommander("irb_120")
hand_group = moveit_commander.MoveGroupCommander("robotiq_85")
display_trajectory_publisher = rospy.Publisher('/move_group/display_planned_path',
                                               moveit_msgs.msg.DisplayTrajectory,
                                               queue_size=20)

# Forward Kinematics (FK): movimiento del grupo robot eje a eje (para robots de 6 ejes). Angulos adaptados a grados

def move_joint_arm(joint_0, joint_1, joint_2, joint_3, joint_4, joint_5):
    joint_goal = arm_group.get_current_joint_values()
    joint_goal[0] = joint_0 * (pi/180)
    joint_goal[1] = joint_1 * (pi/180)
    joint_goal[2] = joint_2 * (pi/180)
    joint_goal[3] = joint_3 * (pi/180)
    joint_goal[4] = joint_4 * (pi/180)
    joint_goal[5] = joint_5 * (pi/180)

    arm_group.go(joint_goal, wait=True)
    arm_group.stop()  # To guarantee no residual movement

# IDEM, para el grupo de la herramienta (un unico eje)

def move_joint_hand(gripper_finger1_joint):
    joint_goal = hand_group.get_current_joint_values()
    joint_goal[2] = gripper_finger1_joint  # Gripper master axis

    hand_group.go(joint_goal, wait=True)
    hand_group.stop()  # To guarantee no residual movement


if __name__ == '__main__':

    # Print estado actual del robot (opcional)
    print("============ Printing robot state ============")
    print(robot.get_current_state())
    print("")

    # Ejemplo: FK en un loop. Movimiento del robot y de la herramienta eje a eje. Angulos en grados (robot). 
    for i in range(2):
        rospy.loginfo("Moving arm to pick pose")
        move_joint_arm(0, 50, -20, 0, 60, 0)
        rospy.sleep(1)
        rospy.loginfo("Closing gripper")
        move_joint_hand(0.5)
        rospy.sleep(1)
        rospy.loginfo("Moving arm to place pose")
        move_joint_arm(150, 20, 10, 0, 60, 90)
        rospy.sleep(1)
        rospy.loginfo("Opening gripper")
        move_joint_hand(0)
        rospy.sleep(1)
        rospy.loginfo("Moving arm to HOME")
        move_joint_arm(0, 0, 0, 0, 45, 0)

    rospy.loginfo("All movements finished. Shutting down")
    moveit_commander.roscpp_shutdown()
