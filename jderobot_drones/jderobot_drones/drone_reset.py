import rclpy
from rclpy.node import Node
import asyncio

from as2_msgs.srv import SetPlatformStateMachineEvent
from as2_msgs.msg import PlatformStateMachineEvent, PlatformStatus

import subprocess
import sys
from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener
from std_srvs.srv import Trigger

class DroneReset(Node):

    def __init__(self):
        super().__init__('quadrotor_reset')
        
        if not rclpy.ok(): 
            rclpy.init()

        drone_id: str = "drone0"
        
        self.state_event_service_client = self.create_client(
            SetPlatformStateMachineEvent, '/' + drone_id + '/platform/state_machine_event')
            
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.reset_service = self.create_service(Trigger, '/quadrotor_reset_pose', self.reset)

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
    
    def reset(self, request, response):
        """Reset the drone position and aerostack state machine"""

        # Get the transform from 'earth' to 'drone0/map'
        from_frame_rel = 'drone0/map'
        to_frame_rel = 'earth'

        self.get_logger().info('Reset service called')  # Add this line
        # # Your reset logic here
        # response.success = True
        # return response

        try:
            t = self.tf_buffer.lookup_transform(
                    to_frame_rel,
                    from_frame_rel,
                    rclpy.time.Time(seconds=0))
        except TransformException as ex:
            self.get_logger().info(
                f'Could not transform {to_frame_rel} to {from_frame_rel}: {ex}')
            response.success = False
            return response
        
        x = t.transform.translation.x
        y = t.transform.translation.y
        z = t.transform.translation.z

        qx = t.transform.rotation.x
        qy = t.transform.rotation.y
        qz = t.transform.rotation.z
        qw = t.transform.rotation.w

        # x = 0
        # y = 0
        # z = 1.449

        # qx = 0
        # qy = 0
        # qz = 0
        # qw = 1
        await self.call_state_event_service(
            PlatformStateMachineEvent.LAND)
        await self.call_state_event_service(
            PlatformStateMachineEvent.LANDED)
        # the gz service to reset model pose
        service = "$(gz service -l | grep '^/world/\w*/set_pose$')"
        reqtype = "gz.msgs.Pose"
        reptype = "gz.msgs.Boolean"
        timeout = "3000"
        # req = f'name: "drone0", position: {{x: {x}, y: {y}, z: {z}}}, orientation: {{x: {qx}, y: {qy}, z: {qz}, w: {qw}}}'
        req = f'name: "drone0", position: {{x: {x}, y: {y}, z: {z}}}'
        command = f"gz service -s {service} --reqtype {reqtype} --reptype {reptype} --timeout {timeout} --req '{req}'"
        self.get_logger().info('Quadrotor position set to its initial value')
        subprocess.call(
            f"{command}",
            shell=True,
            stdout=sys.stdout,
            stderr=subprocess.STDOUT,
            bufsize=1024,
            universal_newlines=True,
        )
        # self.get_logger().info('Quadrotor position set to its initial value')
        # Updating the aerostack state machine to LANDED
        
        response.success = True
        return response

def main(args=None):
    rclpy.init(args=args)

    drone_reset = DroneReset()

    rclpy.spin(drone_reset)

    rclpy.shutdown()


if __name__ == '__main__':
    main()