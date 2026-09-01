import time
import rclpy

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry

CAR_NAMESPACE = "car"
CMD_VEL_TOPIC = "/" + CAR_NAMESPACE + "/cmd_vel"
ODOM_TOPIC = "/" + CAR_NAMESPACE + "/odom"

SPEED = 1.5
X_MIN = -12.0
X_MAX = 12.0

if not rclpy.ok():
    rclpy.init()

node = rclpy.create_node("visual_lander_car")
cmd_pub = node.create_publisher(Twist, CMD_VEL_TOPIC, 10)

car_x = 0.0


def odom_callback(msg):
    global car_x
    car_x = msg.pose.pose.position.x


node.create_subscription(Odometry, ODOM_TOPIC, odom_callback, 10)

direction = 1.0
print("car driving the visual_lander shuttle", flush=True)

while rclpy.ok():
    rclpy.spin_once(node, timeout_sec=0)

    if direction > 0 and car_x >= X_MAX:
        direction = -1.0
    elif direction < 0 and car_x <= X_MIN:
        direction = 1.0

    twist = Twist()
    twist.linear.x = direction * SPEED
    cmd_pub.publish(twist)

    time.sleep(0.05)
