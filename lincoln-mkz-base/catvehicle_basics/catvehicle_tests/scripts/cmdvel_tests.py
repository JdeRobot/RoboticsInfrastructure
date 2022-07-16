#!/usr/bin/env python

import rospy
from std_msgs.msg import String, Float64
from geometry_msgs.msg import Twist, Pose
from sensor_msgs.msg import Joy
import sys, getopt

# requires the ros-indigo-joysticks

class CmdVel:

    def __init__(self):
        rospy.init_node('cmdvel_test')

        rospy.Subscriber('/cmd_vel', Twist, self.callback)
        self.pub_cmdvel = rospy.Publisher("/catvehicle/cmd_vel", Twist, queue_size=1)

        self.x = 0
        self.z = 0

    def callback(self,data):
#        rospy.loginfo(rospy.get_caller_id() + " heard linear=%lf, angular=%lf", data.axes[3], data.axes[0])
        self.x = data.linear.x
        self.z = data.angular.z

    def publish(self):
        msgTwist = Twist()
        msgTwist.linear.x = self.x
        msgTwist.angular.z = self.z
        self.pub_cmdvel.publish(msgTwist)
        
def usage():
    print('cmdveltests -n catvehicle')


def main(argv):

    cmdvel_object = CmdVel()
    rate = rospy.Rate(5) # run at 100Hz
    while not rospy.is_shutdown():
        cmdvel_object.publish()
        rate.sleep()

if __name__ == '__main__':
    main(sys.argv[1:])
    try:
        listener('catvehicle')
    except rospy.ROSInterruptException:
        pass


