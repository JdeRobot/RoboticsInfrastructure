#!/usr/bin/env python
import rospy
from dataspeed_can_msgs.msg import CanMessage

class BusCANObject(object):
    def __init__(self):
        sub = rospy.Subscriber("/can_bus_dbw/can_tx", CanMessage, self.tx_callback)
        
    def tx_callback(self,data):
        rospy.loginfo(rospy.get_caller_id() + ", the dbw_node published this in tx buscan topic ::> %s", str(data))
        
    def listener(self):
        rospy.spin()

if __name__ == '__main__':
    rospy.init_node('obstacle_stopper_node', anonymous=True)
    buscan_object = BusCANObject()
    buscan_object.listener()