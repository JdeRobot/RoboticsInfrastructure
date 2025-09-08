#!/usr/bin/env python3

"""Tests for Line Follower (Simple Circuit) ROS launch file."""

import os
import sys
import unittest
import pytest
import time

import launch_testing
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

import rclpy
from sensor_msgs.msg import Image
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from utils import stop_gazebo  # noqa: E402


@pytest.mark.launch_test
def generate_test_description():
    """Generate the launch description for simple circuit exercise tests."""
    # Get absolute path to the launcher
    launcher_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "Launchers",
        "simple_circuit.launch.py",
    )

    # Start the launch file with arguments
    launch_description = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(launcher_path),
        launch_arguments={"headless": "True", "use_simulator": "True"}.items(),
    )

    return LaunchDescription(
        [
            launch_description,
            launch_testing.actions.ReadyToTest(),
        ]
    )


class TestTopicMsgs(unittest.TestCase):
    """Unit tests for verifying camera topics and images."""

    @classmethod
    def setUpClass(cls):
        """Set up ROS node for testing."""
        rclpy.init()
        cls.node = rclpy.create_node("test_node")

        # wait for topics to be setup
        time.sleep(10)

    @classmethod
    def tearDownClass(cls):
        """Clean up ROS resources after tests."""
        # Clean up ROS resources
        cls.node.destroy_node()
        rclpy.shutdown()
        # Stop any running Gazebo processes
        stop_gazebo()

    def test_odom_works(self, proc_output):
        """Test that the odometry state is updated when the vehicle moves."""
        msgs = []

        # Create a subscription to the odometry topic
        sub = self.__class__.node.create_subscription(
            Odometry,
            "/odom",
            lambda msg: msgs.append(msg),
            qos_profile=10,
        )

        # Wait for messages (up to 1 second)
        for _ in range(10):
            rclpy.spin_once(self.__class__.node, timeout_sec=0.1)
            if msgs:
                break

        # Create a publisher to the velocity topic to trigger odometry updates
        pub = self.__class__.node.create_publisher(
            Twist,
            "/cmd_vel",
            qos_profile=10,
        )

        # Publish a high velocity message to move the vehicle
        twist_msg = Twist()
        twist_msg.linear.x = 45.0  # Move forward at 45 m/s
        twist_msg.angular.z = 120.0  # Turn at 120 rad/s

        # Wait for a short time to allow odometry updates
        for _ in range(10):
            pub.publish(twist_msg)
            rclpy.spin_once(self.__class__.node, timeout_sec=0.1)

        # Check that the vehicle moved by comparing the difference in odom msgs
        self.assertNotAlmostEqual(
            msgs[0].pose.pose.position.x,
            msgs[-1].pose.pose.position.x,
            msg="Odometry messages did not change after publishing velocity.",
        )
        self.assertNotAlmostEqual(
            msgs[0].pose.pose.position.y,
            msgs[-1].pose.pose.position.y,
            msg="Odometry messages did not change after publishing velocity.",
        )

        # Clean up subscriptions
        self.__class__.node.destroy_subscription(sub)
        self.__class__.node.destroy_publisher(pub)

    @unittest.skipIf(
        os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true",
        "Camera tests are unreliable in CI environments",
    )
    def test_camera_images(self, proc_output):
        """Test that camera images are published."""

        # Check actual message receipt
        msgs = []

        # Create subscriptions
        sub_left = self.__class__.node.create_subscription(
            Image,
            "/cam_f1_left/image_raw",
            lambda msg: msgs.append(msg),
            qos_profile=10,
        )

        # Wait for messages (up to 5 seconds)
        for _ in range(50):  # 50 x 0.1 seconds = 5 seconds
            rclpy.spin_once(self.__class__.node, timeout_sec=0.1)
            if msgs:
                break

        # Clean up subscriptions
        self.__class__.node.destroy_subscription(sub_left)

        # Check results
        self.assertGreater(len(msgs), 0, "No images received from left camera")

        print("\n--- Camera Images Test Completed Successfully ---")
