#!/usr/bin/env python3

"""Tests for follow person following camera ROS launch file."""

import os
import sys
import time
import unittest
import pytest

import launch_testing
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

import rclpy
from sensor_msgs.msg import Imu, JointState
from nav_msgs.msg import Odometry

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from utils import stop_gazebo  # noqa: E402


@pytest.mark.launch_test
def generate_test_description():
    """Generate the launch description for follow person following camera tests."""
    # Get absolute path to the launcher
    launcher_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "Launchers",
        "follow_person_followingcam.launch.py",
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


class TestLaunchProcesses(unittest.TestCase):
    """Test for verifying the launch file starts correctly."""

    @classmethod
    def setUpClass(cls):
        """Set up ROS node and initialize test counters before all tests."""
        rclpy.init()
        cls.node = rclpy.create_node("test_node")

        # wait for topics to be setup
        time.sleep(30)

    @classmethod
    def tearDownClass(cls):
        """Clean up ROS node and shutdown rclpy after all tests."""
        cls.node.destroy_node()
        rclpy.shutdown()
        # Stop the gzserver process if it is running
        stop_gazebo()

    def test_joint_state_topics(self, proc_output):
        """Test that the joint state topics are published correctly."""
        # Check if we can get joint state-related topics
        msgs = []
        sub = self.__class__.node.create_subscription(
            JointState,
            "/joint_states",
            lambda msg: msgs.append(msg),
            10,
        )

        # Wait briefly to see if topics are available
        for _ in range(30):
            rclpy.spin_once(self.__class__.node, timeout_sec=0.1)

        # Check if we received any messages
        self.assertGreater(len(msgs), 0, "No messages received on /joint_states topic.")

        self.__class__.node.destroy_subscription(sub)

    def test_imu_and_odom_topics(self, proc_output):
        """Test that the IMU and Odometry topics are published correctly."""

        # Check if we can get IMU-related topics
        imu_msgs = []
        imu_sub = self.__class__.node.create_subscription(
            Imu,
            "/imu",
            lambda msg: imu_msgs.append(msg),
            10,
        )

        # Check if we can get Odometry-related topics
        odom_msgs = []
        odom_sub = self.__class__.node.create_subscription(
            Odometry,
            "/odom",
            lambda msg: odom_msgs.append(msg),
            10,
        )

        # Wait briefly to see if topics are available
        for _ in range(30):
            rclpy.spin_once(self.__class__.node, timeout_sec=0.1)

        # Check if we received any messages
        self.assertGreater(len(imu_msgs), 0, "No messages received on /imu topic.")
        self.assertGreater(len(odom_msgs), 0, "No messages received on /odom topic.")

        self.__class__.node.destroy_subscription(imu_sub)
        self.__class__.node.destroy_subscription(odom_sub)
