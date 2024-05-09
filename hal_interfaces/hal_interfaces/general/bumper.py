from rclpy.node import Node
from gazebo_msgs.msg import ContactsState
from functools import partial


### HAL INTERFACE ###
class BumperNode(Node):

    def __init__(self, topics):
        super().__init__("bumper_node")

        # Hardcoded for the moment to three topics
        # as dynamic callback creation is not trivial
        self.topics = topics
        self.callbacks_ = [
            self.right_callback,
            self.center_callback,
            self.left_callback,
        ]

        # Subscribe to all the callbacks
        for i in range(len(self.topics)):

            self.sub = self.create_subscription(
                ContactsState, topics[i], self.callbacks_[i], 10
            )

        # Right, center, left
        self.contact_states_ = [ContactsState() for _ in range(3)]

    def right_callback(self, contact):
        self.contact_states_[0] = contact

    def center_callback(self, contact):
        self.contact_states_[1] = contact

    def left_callback(self, contact):
        self.contact_states_[1] = contact

    def get_contact(self, index):
        return self.contact_states_[index]
