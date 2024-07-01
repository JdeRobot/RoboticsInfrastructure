from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
import rosgraph_msgs.msg

### AUXILIARY FUNCTIONS
class SimTime():
    def __init__(self):
        self.sec = 0
        self.nanosec = 0
    
    def __str__(self):
        s = (
            "SimTime: {\n   sec:" 
            + str(self.sec) 
            + "\n   nanosec: " 
            + str(self.nanosec) 
            + "\n}"
            )
        
        return s

def clock2SimTime(clock):
    """
    Translates from ROS Clock to JderobotTypes SimTime.
    @param clock: ROS Clock to translate
    @type clock: Clock
    @return a SimTime translated from clock
    """
    simtime = SimTime()
    simtime.sec = clock.clock.sec
    simtime.nanosec = clock.clock.nanosec

    return simtime
    
### HAL INTERFACE ###
class SimTimeNode(Node):
    def __init__(self, topic):
        super().__init__("simtime_node")

        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        self.sub = self.create_subscription(
            rosgraph_msgs.msg.Clock, 
            topic, 
            self.listener_callback, 
            qos_profile=qos_profile
        )

        self.last_simtime_ = rosgraph_msgs.msg.Clock()

    def listener_callback(self, clock):
        self.last_simtime_ = clock
    
    def getSimTime(self):
        return clock2SimTime(self.last_simtime_)