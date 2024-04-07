from rclpy.node import Node
from gazebo_msgs.msg import ContactsState
from functools import partial


### AUXILIARY FUNCTIONS ###
class BumperData:

    def __init__(self):

        self.pressed_bumpers = []  # Indicates which bumpers are pressed
        self.timeStamp = 0  # Time stamp [s]

    def __str__(self):
        s = "BumperData: {\n   pressed bumpers: " + str(self.bumpers)
        s = s + "\n   timeStamp: " + str(self.timeStamp) + "\n}"
        return s


def contactsStateList2BumperData(bumper_msg_list_):
    """
    Translates from ROS ContactsState to JderobotTypes BumperData.
    @param event: ROS ContactsState to translate
    @type event: ContactsState
    @return a BumperData translated from event

    # bumpers
    Same order as in the topics list
    """
    bump = BumperData()
    latest_timestamp = 0
    n_bumpers_ = len(bumper_msg_list_)

    # Add the pressed bumpers, calculating the latest timestamp
    for i in range(n_bumpers_):
        if len(bumper_msg_list_[i].states) > 0:
            bump.pressed_bumpers.append(i)

        msg_timestamp = bumper_msg_list_[i].header.stamp.sec + (
            bumper_msg_list_[i].header.stamp.nanosec * 1e-9
        )
        latest_timestamp = max(latest_timestamp, msg_timestamp)

    bump.timeStamp = latest_timestamp

    return bump


### HAL INTERFACE ###
class BumperNode(Node):

    def __init__(self, topics):
        super().__init__("bumper_node")
        self.topics = topics
        self.subs = []
        self.n_bumpers_ = len(topics)
        self.last_bumper_msgs_ = [ContactsState() for _ in range(self.n_bumpers_)]

        for i in range(self.n_bumpers_):
            sub = self.create_subscription(
                ContactsState,
                self.topics[i],
                partial(self.callback, index=i),
                10,
            )
            self.subs.append(sub)

    def callback(self, msg, index):
        self.last_bumper_msgs_[index] = msg

    def getBumperData(self):
        return contactsStateList2BumperData(self.last_bumper_msgs_)
