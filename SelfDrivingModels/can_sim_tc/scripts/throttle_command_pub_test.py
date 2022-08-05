#!/usr/bin/env python
# license removed for brevity
import rospy
import random
from dbw_mkz_msgs.msg import ThrottleCmd
from dataspeed_can_msgs.msg import CanMessage
from std_msgs.msg import Empty

"""
dbw_mkz_msgs/Throttle

# Throttle pedal
# Options defined below
float32 pedal_cmd
uint8 pedal_cmd_type

# Enable
bool enable

# Ignore driver overrides
bool ignore

# Watchdog counter (optional)
uint8 count

uint8 CMD_NONE=0
uint8 CMD_PEDAL=1   # Unitless, range 0.15 to 0.80
uint8 CMD_PERCENT=2 # Percent of maximum throttle, range 0 to 1

"""
"""
rosmsg show  dataspeed_can_msgs/CanMessage
uint8[8] data
uint32 id
bool extended
uint8 dlc
"""

def callback(data):
    rospy.loginfo(rospy.get_caller_id() + ", the dbw_node published this in tx buscan topic ::> %s", str(data))

def can_bus_tx_reader():
    sub = rospy.Subscriber("/can_bus_dbw/can_tx", CanMessage, callback)

def cmd_publisher():
    """
    This makes the simulated function of a real Throttle pedal pressed
    :return:
    """
    pub = rospy.Publisher('/vehicle/throttle_cmd', ThrottleCmd, queue_size=1)
    pub_enable = rospy.Publisher('/vehicle/enable', Empty, queue_size=1)
    can_bus_tx_reader()
    rospy.init_node('can_bus_reader_publisher_topic_throttle_publisher', anonymous=True)
    rate = rospy.Rate(1)

    # We wait for the Gazebo system to be available pefore publishing anything
    rospy.wait_for_service('/gazebo/set_physics_properties')
    rospy.loginfo("Gazebo Ready...")
    # We publish enable to enable dbw allow commands from outside
    """
    rostopic pub /vehicle/enable std_msgs/Empty "{}"
    """
    empty_message = Empty()
    pub_enable.publish(empty_message)

    while not rospy.is_shutdown():
        msg_str = "Publishing Brake message in /vehicle/brake_cmd %s" % rospy.get_time()
        rospy.loginfo(msg_str)
        throttle_command_object = ThrottleCmd()
        throttle_command_object.pedal_cmd = random.uniform(0.0, 0.8)
        #throttle_command_object.pedal_cmd = 0.7
        throttle_command_object.pedal_cmd_type = 1
        throttle_command_object.enable = False
        throttle_command_object.ignore = False
        throttle_command_object.count = 0
        rospy.loginfo("Start Publish ::>"+str(throttle_command_object))
        pub.publish(throttle_command_object)
        rospy.loginfo("End publish, waiting...")
        rate.sleep()
        rospy.loginfo("Ended waiting")



if __name__ == '__main__':
    try:
        cmd_publisher()
    except rospy.ROSInterruptException:
        print "Exception occured"
        pass