from rclpy.node import Node
from std_msgs.msg import String

def cmdLift2String(cmdLift):
    return cmdLift.msg

class CMDLift ():

    def __init__(self):
        self.msg = String()
        self.msg.data = "unload"
    
    def cmd(self,cmd):
        self.msg.data = cmd

    def __str__(self):
        return "CMDlift:" + self.msg.data


### HAL INTERFACE ###
class PublisherPlatformNode(Node):

    def __init__(self, topic):

        super().__init__("PublisherPlatform")
        self.pub = self.create_publisher(String, topic, 10)
        self.data = CMDLift()

    def load(self):
        self.data.cmd("load")
        self.pub.publish(cmdLift2String(self.data))

    def unload(self):
        self.data.cmd("unload")
        self.pub.publish(cmdLift2String(self.data))

