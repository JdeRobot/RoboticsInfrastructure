import launch
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='usb_cam',
            executable='usb_cam_node',
            name='usb_cam_node',
            parameters=[
                {'video_device': '/dev/video0'}
            ],
        ),
    ])


