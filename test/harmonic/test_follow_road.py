#!/usr/bin/env python3

"""Tests for the Vacuum Cleaner (no localization) ROS launch file."""

import os
import sys
import unittest
import pytest
import time

import launch_testing
from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
)
from launch.launch_description_sources import (
    PythonLaunchDescriptionSource,
)

import rclpy
from std_msgs.msg import Bool
from geometry_msgs.msg import Twist, PoseStamped
from sensor_msgs.msg import Imu

from rclpy.qos import (
    QoSProfile,
    QoSReliabilityPolicy,
    QoSHistoryPolicy,
)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import stop_gazebo  # noqa: E402


@pytest.mark.launch_test
def generate_test_description():
    """Generate the launch description for simple circuit exercise tests."""
    # Get absolute path to the launcher
    launcher_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "..",
        "Launchers",
        "follow_road.launch.py",
    )

    config_file = "/opt/jderobot/jderobot_drones/sim_config/gzsim/world.json"

    # Start the launch file with arguments
    launch_description = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(launcher_path),
        launch_arguments={
            "headless": "True",
            "use_simulator": "True",
            "use_sim_time": "True",
            "simulation_config_file": config_file,
            "plugin_name": "differential_flatness_controller",
            # "plugin_name": "pid_speed_controller",
        }.items(),
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
        time.sleep(15)

    @classmethod
    def tearDownClass(cls):
        """Clean up ROS resources after tests."""
        # Clean up ROS resources
        cls.node.destroy_node()
        rclpy.shutdown()
        # Stop any running Gazebo processes
        stop_gazebo()

    def test_imu_works(self, proc_output):
        """Test that the imu topic works."""
        msgs = []

        sub = self.__class__.node.create_subscription(
            Imu,
            "/drone0/sensor_measurements/imu",
            lambda msg: msgs.append(msg),
            qos_profile=10,
        )

        # Wait for messages (up to 1 second)
        for _ in range(10):
            rclpy.spin_once(
                self.__class__.node,
                timeout_sec=0.1,
            )
            if msgs:
                break

        # Check that we received msgs
        self.assertGreater(
            len(msgs),
            0,
            msg="No IMU messages received.",
        )

        # Clean up subscriptions
        self.__class__.node.destroy_subscription(sub)

    def test_movement_works(self, proc_output):
        """Test that the velocity topic works correctly."""
        msgs = []

        sub_qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
        )

        pub_qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
        )

        # Create a subscription to the velocity topic
        sub = self.__class__.node.create_subscription(
            PoseStamped,
            "/drone0/ground_truth/pose",
            lambda msg: msgs.append(msg),
            qos_profile=sub_qos_profile,
        )

        arm_pub = self.__class__.node.create_publisher(
            Bool,
            "/gz/drone0/arm",
            qos_profile=pub_qos_profile,
        )

        # Create a publisher to the velocity topic
        pub = self.__class__.node.create_publisher(
            Twist,
            "/gz/drone0/cmd_vel",
            qos_profile=pub_qos_profile,
        )

        # Publish a high velocity message to move the vehicle
        twist_msg = Twist()
        twist_msg.linear.x = 1.0  # Move forward at 1 m/s
        twist_msg.angular.z = 0.1  # Turn at 10 rad/s

        arm_pub.publish(Bool(data=True))
        rclpy.spin_once(
            self.__class__.node,
            timeout_sec=0.1,
        )
        # Wait for a short time to allow odometry updates
        for _ in range(100):
            pub.publish(twist_msg)
            rclpy.spin_once(
                self.__class__.node,
                timeout_sec=0.1,
            )
        # Check that we received some messages
        self.assertNotAlmostEqual(
            msgs[-1].pose.position.x,
            msgs[0].pose.position.x,
            msg="Drone did not move.",
        )
        self.assertNotEqual(
            len(msgs),
            0,
            msg="No cmd_vel messages received.",
        )

        # Clean up subscriptions
        self.__class__.node.destroy_subscription(sub)
        self.__class__.node.destroy_publisher(pub)
