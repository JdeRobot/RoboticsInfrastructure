"""
drone_wrapper.py
"""
import asyncio
import time
from typing import List
from numpy import ndarray

from as2_python_api.drone_interface_base import DroneInterfaceBase
from as2_python_api.modules.motion_reference_handler_module import MotionReferenceHandlerModule
from as2_msgs.srv import SetPlatformStateMachineEvent
from as2_msgs.msg import PlatformStateMachineEvent, PlatformStatus

from sensor_msgs.msg import Image
from geometry_msgs.msg import TwistStamped
from cv_bridge import CvBridge
import rclpy
from rclpy.qos import QoSProfile, QoSHistoryPolicy, QoSReliabilityPolicy, QoSDurabilityPolicy


class DroneWrapper(DroneInterfaceBase):
    """
    Drone Wrapper
    """
    TK_RATE = 0.1
    TK_HEIGHT_MARGIN = 0.25
    LAND_RATE = 0.1
    LAND_SPEED = 0.5
    LAND_SPEED_MARGIN = 0.1
    LAND_HEIGHT_MARGIN = 0.1

    def __init__(self, drone_id: str = "drone0", verbose: bool = False) -> None:
        super().__init__(drone_id, verbose, use_sim_time=False)

        yaw_rate_topic = '/' + drone_id + '/self_localization/twist'

        self.yaw_rate = 0.0

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
        self.yaw_subscription  # prevent unused variable warning

        self.motion_ref_handler = MotionReferenceHandlerModule(drone=self)

        self.state_event_service_client = self.create_client(
            SetPlatformStateMachineEvent, '/' + drone_id + '/platform/state_machine_event')

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

    def yaw_rate_cb(self, msg: TwistStamped):
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
        DISARMED    0
        LANDED      1
        TAKING_OFF  2
        FLYING      3
        LANDING     4

        :rtype: int
        """
        return self.info["state"]

    def set_cmd_pos(self, x: float, y: float, z: float, az: float) -> None:
        """Send position command with yaw angle"""
        self.motion_ref_handler.position.send_position_command_with_yaw_angle(
            [x, y, z], 1.0, 'earth', self.namespace + '/base_link', float(az))

    def set_cmd_vel(self, vx: float, vy: float, vz: float, az: float) -> None:
        """Send speed command with yaw angle"""
        self.motion_ref_handler.speed.send_speed_command_with_yaw_speed(
            [vx, vy, vz], self.namespace + '/base_link', float(az))

    def set_cmd_mix(self, vx: float, vy: float, z: float, az: float) -> None:
        """Send speed in a plane command with yaw angle"""
        self.motion_ref_handler.speed_in_a_plane.send_speed_in_a_plane_command_with_yaw_speed(
            [vx, vy], z, 'earth', self.namespace + '/base_link', float(az))

    async def call_state_event_service(self, event_value: PlatformStateMachineEvent) -> None:
        """Request aerostack to update state machine given the new event
        EMERGENCY  -1
        DISARMED    0
        LANDED      1
        TAKING_OFF  2
        FLYING      3
        LANDING     4
        """
        request = SetPlatformStateMachineEvent.Request()
        request.event.event = event_value

        while not self.state_event_service_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Service not available, waiting...')

        response = await self.state_event_service_client.call_async(request)

        if response is not None:
            self.get_logger().info(f'Success: {response.success}')
            self.get_logger().info(f'Current State: {response.current_state}')
        else:
            self.get_logger().error('Service call failed')

    def takeoff(self, height: float):
        """Send Takeoff command with height"""
        if self.get_landed_state() == PlatformStatus.TAKING_OFF or \
                self.get_landed_state() == PlatformStatus.FLYING:
            self.get_logger().info('Drone is already flying!')
            return

        self.arm()
        self.offboard()

        # Starting to take off
        asyncio.run(self.call_state_event_service(
            PlatformStateMachineEvent.TAKE_OFF))

        while True:
            if abs(self.position[2] - height) < self.TK_HEIGHT_MARGIN:
                break
            self.set_cmd_pos(
                self.position[0], self.position[1], height, self.get_yaw())
            time.sleep(self.TK_RATE)

        # Take off finished
        asyncio.run(self.call_state_event_service(
            PlatformStateMachineEvent.TOOK_OFF))

    def land(self) -> None:
        """Send Landing command"""

        if self.get_landed_state() == PlatformStatus.LANDED or \
                self.get_landed_state() == PlatformStatus.LANDING:
            self.get_logger().info('Drone is already landed!')
            return

        # Starting to land
        asyncio.run(self.call_state_event_service(
            PlatformStateMachineEvent.LAND))

        height = self.position[2]
        while True:
            self.set_cmd_vel(0, 0, -self.LAND_SPEED, 0.0)
            time.sleep(self.LAND_RATE)

            # Check if drone has landed
            if abs(self.get_velocity()[2]) < self.LAND_SPEED_MARGIN and \
                    abs(self.position[2] - height) > self.LAND_HEIGHT_MARGIN:
                break

        # Land finished
        asyncio.run(self.call_state_event_service(
            PlatformStateMachineEvent.LANDED))

        self.disarm()


def main(args=None):
    rclpy.init(args=args)
    drone = DroneWrapper()
    rclpy.spin(drone)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
