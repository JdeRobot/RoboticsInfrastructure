#!/usr/bin/env python
# license removed for brevity
import rospy
from dbw_mkz_msgs.msg import BrakeCmd
from dataspeed_can_msgs.msg import CanMessage

"""
dbw_mkz_msgs/BrakeCmd

uint8 CMD_NONE=0
uint8 CMD_PEDAL=1
uint8 CMD_PERCENT=2
uint8 CMD_TORQUE=3
float32 TORQUE_BOO=520
float32 TORQUE_MAX=3412
float32 pedal_cmd
uint8 pedal_cmd_type
bool boo_cmd
bool enable
bool ignore
uint8 count
"""
"""
rosmsg show  dataspeed_can_msgs/CanMessage
uint8[8] data
uint32 id
bool extended
uint8 dlc
"""

def callback(data):
    rospy.loginfo(rospy.get_caller_id() + "I heard %s", str(data))

def can_bus_tx_reader():
    sub = rospy.Subscriber("/can_bus_dbw/can_tx", CanMessage, callback)

def brake_cmd_publisher():
    pub = rospy.Publisher('/vehicle/brake_cmd', BrakeCmd, queue_size=1)
    can_bus_tx_reader()
    rospy.init_node('can_bus_reader_publisher_topic_brake_publisher', anonymous=True)
    rate = rospy.Rate(1) # 10hz
    while not rospy.is_shutdown():
        msg_str = "Publishing Brake message in /vehicle/brake_cmd %s" % rospy.get_time()
        rospy.loginfo(msg_str)
        brake_command_object = BrakeCmd()
        brake_command_object.pedal_cmd = 0.0
        brake_command_object.pedal_cmd_type = 0
        brake_command_object.boo_cmd = False
        brake_command_object.enable = False
        brake_command_object.ignore = False
        brake_command_object.count = 0
        rospy.loginfo("Start Publish")
        pub.publish(brake_command_object)
        rospy.loginfo("End publish, waiting...")
        rate.sleep()
        rospy.loginfo("Ended waiting")

if __name__ == '__main__':
    try:
        brake_cmd_publisher()
    except rospy.ROSInterruptException:
        print "Exception occured"
        pass