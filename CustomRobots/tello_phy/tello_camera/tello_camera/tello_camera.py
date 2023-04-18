import rclpy
from rclpy.node import Node
import cv2 

from sensor_msgs.msg import Image
from cv_bridge import CvBridge


class telloCam(Node):

    def __init__(self):
        super().__init__('tello_camera_node')
        self.subscription = self.create_subscription(
            Image,
            '/image_raw',
            self.listener_callback,
            10)
        self.br = CvBridge()

    def listener_callback(self, img):
        print("Callback")
        current_frame = self.br.imgmsg_to_cv2(img)
        hsv_img = cv2.cvtColor(current_frame, cv2.COLOR_BGR2HSV)
        cv2.imshow('HSV image', hsv_img)
        cv2.waitKey(1)


def main(args=None):
    rclpy.init(args=args)

    minimal_subscriber = telloCam()

    
    rclpy.spin(minimal_subscriber)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    minimal_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()