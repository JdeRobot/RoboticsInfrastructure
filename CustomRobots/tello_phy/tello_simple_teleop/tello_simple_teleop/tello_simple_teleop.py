import sys
import time

from tello_msgs.srv import TelloAction
import rclpy
from rclpy.node import Node


class MinimalClientAsync(Node):

    def __init__(self):
        super().__init__('minimal_client_async')
        self.cli = self.create_client(TelloAction, 'tello_action')
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')
        self.req = TelloAction.Request()

    def send_request(self, cmd):
        self.req.cmd = cmd
        self.future = self.cli.call_async(self.req)
        rclpy.spin_until_future_complete(self, self.future)


def main(args=None):
    rclpy.init(args=args)

    minimal_client = MinimalClientAsync()
    response = minimal_client.send_request('takeoff')
    
    time.sleep(2)
    
    response = minimal_client.send_request('stop')

    minimal_client.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()