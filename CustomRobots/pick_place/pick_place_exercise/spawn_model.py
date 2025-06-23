#!/usr/bin/env python3
import rospy
from gazebo_msgs.srv import SpawnModel, DeleteModel
from geometry_msgs.msg import Pose, Quaternion
from tf.transformations import euler_from_quaternion, quaternion_from_euler


def pose2msg(x, y, z, roll, pitch, yaw):
    pose = Pose()
    pose.position.x = x
    pose.position.y = y
    pose.position.z = z
    quat = quaternion_from_euler(roll, pitch, yaw)
    pose.orientation.x = quat[0]
    pose.orientation.y = quat[1]
    pose.orientation.z = quat[2]
    pose.orientation.w = quat[3]
    return pose


if __name__ == "__main__":
    print("spawning seleted model")
    rospy.init_node("spawn_model")
    rospy.wait_for_service("gazebo/spawn_sdf_model")
    spawn_model = rospy.ServiceProxy("gazebo/spawn_sdf_model", SpawnModel)

    model_name = "red_box"

    # Actualizar la ruta de la carpeta por la correcta:
    with open(
        "/home/diego/ws_moveit/src/irb120_robotiq85/irb120_robotiq85_gazebo/models/{}/model.sdf".format(
            model_name
        ),
        "r",
    ) as f:
        model_xml = f.read()

    # Posición y orientacion del objeto
    model_pose = pose2msg(0.5, 0, 0, 0, 0, 0)

    spawn_model(model_name, model_xml, "", model_pose, "world")
