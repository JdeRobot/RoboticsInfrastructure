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

# INVERSE KINEMATICS (cartesiana, equivalente a moveL)
# Creación de una trayectoria lineal PUNTO A PUNTO
# Usamos una lista vacia en la que insertamos los puntos esquina de la trayectoria lineal
waypoints = []
	
# Position 1, lateral (incremento en y)
wpose = arm_group.get_current_pose().pose
wpose.position.y += 0.2 
waypoints.append(copy.deepcopy(wpose))

# Position 2, lateral (coordenadas absolutas)
wpose.position.x = 0
wpose.position.y = 0.5
wpose.position.z = 0.5  
waypoints.append(copy.deepcopy(wpose))

# Position 3, sobre el robot (coordenadas absolutas)
wpose.position.x = 0.2
wpose.position.y = 0
wpose.position.z = 0.7
waypoints.append(copy.deepcopy(wpose))

# Position 4, otro lateral (coordenadas absolutas)
wpose.position.x = 0
wpose.position.y = -0.5
wpose.position.z = 0.5  
waypoints.append(copy.deepcopy(wpose))

# Position 5, frontal (coordenadas absolutas)
wpose.position.x = 0.5
wpose.position.y = 0
wpose.position.z = 0.3  
waypoints.append(copy.deepcopy(wpose))

# Mantenemos la definicion de este método de IK equivalente al MoveJ por comodidad
def move_pose_arm(roll, pitch, yaw, x, y, z):
    pose_goal = geometry_msgs.msg.Pose()
    quat = quaternion_from_euler(roll*(pi/180), pitch*(pi/180), yaw*(pi/180))
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
    
if __name__ == '__main__':

	# Movimiento a posicion HOME inicial (no cartesiano)
	rospy.loginfo("Moving arm to HOME point")	
	move_pose_arm(0, 90, 0, 0.4, 0, 0.6)
	rospy.sleep(1)

	# Planificación de la trayectoria cartesiana entre waypoints
	# Se calcula una configuración de robot por cada "eef_step" en metros
	# El "jump_threshold" especifica la distancia maxima entre puntos consecutivos del espacio de configuracion del robot (dejar a 0)
	# El metodo devuelve la fraccion de la trayectoria que se ha podido seguir
	(plan, fraction) = arm_group.compute_cartesian_path(
		                           waypoints,   # waypoints a seguir
		                           0.01,        # eef_step
		                           0.0)         # jump_threshold
	rospy.loginfo("Cartesian path planned")	

	# RVIZ trajectory visualization
	display_trajectory = moveit_msgs.msg.DisplayTrajectory()
	display_trajectory.trajectory_start = robot.get_current_state()
	display_trajectory.trajectory.append(plan)
	display_trajectory_publisher.publish(display_trajectory); # Publish

	# Complete trajectory execution
	arm_group.execute(plan, wait=True)
	rospy.loginfo("Cartesian path finished. Shutting down")	
	moveit_commander.roscpp_shutdown()
