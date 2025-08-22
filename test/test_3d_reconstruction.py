#!/usr/bin/env python3

"""Tests for 3D reconstruction ROS launch file."""

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
from sensor_msgs.msg import CameraInfo, Image

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from utils import stop_gazebo  # noqa: E402


@pytest.mark.launch_test
def generate_test_description():
    """Generate the launch description for 3D reconstruction tests."""
    # Get absolute path to the launcher
    launcher_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "Launchers",
        "3d_reconstruction.launch.py",
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

    @unittest.skipIf(
        os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true",
        "Camera tests are unreliable in CI environments",
    )
    def test_camera_topics(self, proc_output):
        """Test that camera topics are publishing msgs."""

        msgs_left = []
        msgs_right = []

        # Create subscriptions
        sub_left = self.__class__.node.create_subscription(
            CameraInfo,
            "/cam_turtlebot_left/camera_info",
            lambda msg: msgs_left.append(msg),
            qos_profile=10,
        )

        sub_right = self.__class__.node.create_subscription(
            CameraInfo,
            "/cam_turtlebot_right/camera_info",
            lambda msg: msgs_right.append(msg),
            qos_profile=10,
        )

        # Wait for messages (up to 5 seconds)
        for _ in range(50):  # 50 x 0.1 seconds = 5 seconds
            rclpy.spin_once(self.__class__.node, timeout_sec=0.1)
            if msgs_left and msgs_right:
                break

        # Clean up subscriptions
        self.__class__.node.destroy_subscription(sub_left)
        self.__class__.node.destroy_subscription(sub_right)

        # Check results
        self.assertGreater(len(msgs_left), 0, "No messages received from left camera")
        self.assertGreater(len(msgs_right), 0, "No messages received from right camera")

        print("\n--- Camera Topics Test Completed Successfully ---")

    @unittest.skipIf(
        os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true",
        "Camera tests are unreliable in CI environments",
    )
    def test_camera_images(self, proc_output):
        """Test that camera images are published."""

        # Check actual message receipt
        msgs_left = []
        msgs_right = []

        # Create subscriptions
        sub_left = self.__class__.node.create_subscription(
            Image,
            "/cam_turtlebot_left/image_raw",
            lambda msg: msgs_left.append(msg),
            qos_profile=10,
        )

        sub_right = self.__class__.node.create_subscription(
            Image,
            "/cam_turtlebot_right/image_raw",
            lambda msg: msgs_right.append(msg),
            qos_profile=10,
        )

        # Wait for messages (up to 5 seconds)
        for _ in range(50):  # 50 x 0.1 seconds = 5 seconds
            rclpy.spin_once(self.__class__.node, timeout_sec=0.1)
            if msgs_left and msgs_right:
                break

        # Clean up subscriptions
        self.__class__.node.destroy_subscription(sub_left)
        self.__class__.node.destroy_subscription(sub_right)

        # Check results
        self.assertGreater(len(msgs_left), 0, "No images received from left camera")
        self.assertGreater(len(msgs_right), 0, "No images received from right camera")

        print("\n--- Camera Images Test Completed Successfully ---")
