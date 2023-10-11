import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from rclpy.qos import QoSProfile, QoSHistoryPolicy, QoSReliabilityPolicy, QoSDurabilityPolicy
from cv_bridge import CvBridge
from numpy import ndarray
import threading
import rclpy.executors


class ImageSubscriberNode(Node):
    def __init__(self):
        super().__init__('image_subscriber_node')

        cam_frontal_topic = '/' + 'drone0' + \
            '/sensor_measurements/frontal_camera/image_raw'
        cam_ventral_topic = '/' + 'drone0' + \
            '/sensor_measurements/ventral_camera/image_raw'

        self.frontal_image = Image()
        self.ventral_image = Image()

        self.bridge = CvBridge()
        self.keep_running = True
        self.__executor = rclpy.executors.SingleThreadedExecutor()
        self.__executor.add_node(self)
        self.spin_thread = threading.Thread(target=self.__auto_spin)
        self.spin_thread.start()

        qos_profile = QoSProfile(
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE
        )
        self.cam_frontal_subscription = self.create_subscription(
            Image,
            cam_frontal_topic,
            self.cam_frontal_cb,
            qos_profile)
        self.cam_frontal_subscription  # prevent unused variable warning

        self.cam_ventral_subscription = self.create_subscription(
            Image,
            cam_ventral_topic,
            self.cam_ventral_cb,
            qos_profile)
        self.cam_ventral_subscription  # prevent unused variable warning

    def __auto_spin(self) -> None:
        """Drone inner spin"""
        while self.keep_running and rclpy.ok():
            self.__executor.spin_once(timeout_sec=0)

    def cam_frontal_cb(self, msg):
        """Callback to update current Frontal Image"""
        self.frontal_image = msg


    def cam_ventral_cb(self, msg):
        """Callback to update current Ventral Image"""
        self.ventral_image = msg

    def get_frontal_image(self) -> ndarray:
        """Get drone front view.

        :rtype: numpy.ndarray
        """
        return self.bridge.imgmsg_to_cv2(self.frontal_image)

    def get_ventral_image(self) -> ndarray:
        """Get drone ventral view.

        :rtype: numpy.ndarray
        """
        return self.bridge.imgmsg_to_cv2(self.ventral_image)


def main(args=None):
    rclpy.init(args=args)
    node = ImageSubscriberNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
   main()
