"""
drone_wrapper.py
"""
from typing import List
from numpy import ndarray

from as2_python_api.drone_interface_base import DroneInterfaceBase
from as2_python_api.modules.motion_reference_handler_module import MotionReferenceHandlerModule
from as2_python_api.modules.takeoff_module import TakeoffModule
from as2_python_api.modules.land_module import LandModule

from sensor_msgs.msg import Image
from geometry_msgs.msg import TwistStamped
from cv_bridge import CvBridge
import rclpy
from rclpy.qos import QoSProfile, QoSHistoryPolicy, QoSPresetProfiles, QoSReliabilityPolicy, QoSDurabilityPolicy



class DroneWrapper(DroneInterfaceBase):
    """
    Drone Wrapper
    """

    def __init__(self, drone_id: str = "drone0", verbose: bool = False,
                 use_sim_time: bool = False) -> None:
        super().__init__(drone_id, verbose, use_sim_time)

        yaw_rate_topic = '/' + drone_id + '/self_localization/twist'
        cam_frontal_topic = '/' + drone_id + '/sensor_measurements/hd_camera/image_raw'
        cam_ventral_topic = '/' + drone_id + '/sensor_measurements/hd_camera/image_raw'

        self.yaw_rate = 0.0
        self.frontal_image = Image()
        self.ventral_image = Image()

        self.bridge = CvBridge()

        qos_profile = QoSProfile(
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE
        )

        self.yaw_subscription = self.create_subscription(
            TwistStamped,
            yaw_rate_topic,
            self.yaw_rate_cb,
            qos_profile)
        self.yaw_subscription

        self.cam_frontal_subscription = self.create_subscription(
            Image,
            cam_frontal_topic,
            self.cam_frontal_cb,
            qos_profile)
        self.cam_frontal_subscription

        self.cam_ventral_subscription = self.create_subscription(
            Image,
            cam_ventral_topic,
            self.cam_ventral_cb,
            qos_profile)
        self.cam_ventral_subscription

        self.motion_ref_handler = MotionReferenceHandlerModule(drone=self)
        self.takeoff_module = TakeoffModule(drone=self)
        self.land_module = LandModule(drone=self)

    def get_position(self) -> List[float]:
        """Get drone position (x, y, z) in m.

        :rtype: List[float]
        """
        return self.position

    def get_velocity(self) -> List[float]:
        """Get drone speed (vx, vy, vz) in m/s.

        :rtype: List[float]
        """
        return self.speed

    def yaw_rate_cb(self, msg):
        """Callback to update current Yaw Rate"""
        self.yaw_rate = msg.twist.angular.z

    def get_yaw_rate(self) -> float:
        """Get drone yaw rate az in m/s.

        :rtype: float
        """
        return self.yaw_rate

    def get_orientation(self) -> List[float]:
        """Get drone orientation (roll, pitch, yaw) in rad.

        :rtype: List[float]
        """
        return self.orientation

    def get_roll(self) -> float:
        """Get drone roll in rad.

        :rtype: float
        """
        return self.orientation[0]

    def get_pitch(self) -> float:
        """Get drone pitch in rad.

        :rtype: float
        """
        return self.orientation[1]

    def get_yaw(self) -> float:
        """Get drone yaw in rad.

        :rtype: float
        """
        return self.orientation[2]

    def get_landed_state(self) -> int:
        """Get drone state in int.
        EMERGENCY  -1
        DISARMED	0
        LANDED	    1
        TAKING_OFF	2
        FLYING	    3
        LANDING	    4

        :rtype: int
        """
        return self.info["state"]

    def set_cmd_pos(self, x: float, y: float, z: float, az: float) -> None:
        """Send position command with yaw angle"""
        self.motion_ref_handler.position.send_position_command_with_yaw_angle([x, y, z], 1.0, 'earth', 'earth', az)

    def set_cmd_vel(self, vx: float, vy: float, vz: float, az: float) -> None:
        """Send position command with yaw speed"""
        self.motion_ref_handler.position.send_position_command_with_yaw_speed([x, y, z],'earth', az)

    def set_cmd_mix(self, vx: float, vy: float, z: float, az: float) -> None:
        raise NotImplementedError

    def takeoff(self, height: float):
        """Send Takeoff command with height"""
        self.arm()
        self.offboard()
        self.takeoff_module(height)

    def land(self) -> None:
        """Send Landing command"""
        self.land_module()

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
    drone = DroneWrapper()
    rclpy.spin(drone)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
