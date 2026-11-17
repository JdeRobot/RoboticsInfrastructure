#!/usr/bin/env python3

"""Launch tests for Roomba / Vacuum Cleaner modular robot."""

import os
import sys
import unittest
import pytest
import time

import launch_testing
import launch_testing.actions
from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    AppendEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

import rclpy
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from ros_gz_interfaces.msg import Contacts

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from utils import stop_gazebo  # noqa: E402


@pytest.mark.launch_test
def generate_test_description():
    """Generate the launch description for Roomba / vacuum cleaner robot tests."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Path to vacuum cleaner launcher
    vacuum_launcher_path = os.path.join(
        repo_root,
        "CustomRobots",
        "vacuum_cleaner",
        "launch",
        "vacuum_cleaner.launch.py",
    )
    if not os.path.exists(vacuum_launcher_path):
        try:
            custom_robots_dir = get_package_share_directory("custom_robots")
            for candidate in [
                os.path.join(custom_robots_dir, "vacuum_cleaner", "launch", "vacuum_cleaner.launch.py"),
                os.path.join(custom_robots_dir, "launch", "vacuum_cleaner.launch.py"),
            ]:
                if os.path.exists(candidate):
                    vacuum_launcher_path = candidate
                    break
        except Exception:
            pass

    ros_gz_sim = get_package_share_directory("ros_gz_sim")

    # Start headless Gazebo simulation
    gazebo_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": "-r -s -v4 empty.sdf",
            "on_exit_shutdown": "true",
        }.items(),
    )

    # Launch vacuum cleaner in the vacuum_cleaner namespace
    vacuum_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(vacuum_launcher_path),
        launch_arguments={
            "use_sim_time": "true",
            "namespace": "vacuum_cleaner",
            "entity": "vacuum_cleaner",
            "sensor": "laser",
        }.items(),
    )

    # Add model resource paths
    models_path = os.path.join(repo_root, "CustomRobots", "vacuum_cleaner", "models")
    if not os.path.exists(models_path):
        try:
            custom_robots_dir = get_package_share_directory("custom_robots")
            for candidate in [
                os.path.join(custom_robots_dir, "vacuum_cleaner", "models"),
                os.path.join(custom_robots_dir, "models"),
            ]:
                if os.path.exists(candidate):
                    models_path = candidate
                    break
        except Exception:
            pass
    set_env_res = SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", models_path)
    append_env_res = AppendEnvironmentVariable("GZ_SIM_RESOURCE_PATH", models_path)

    return LaunchDescription(
        [
            set_env_res,
            append_env_res,
            gazebo_server,
            vacuum_cmd,
            launch_testing.actions.ReadyToTest(),
        ]
    )


class TestRoomba(unittest.TestCase):
    """Unit tests for verifying Roomba topics, sensors, bumpers, and teleoperation."""

    @classmethod
    def setUpClass(cls):
        """Set up ROS 2 node for testing."""
        rclpy.init()
        cls.node = rclpy.create_node("test_roomba_node")

        # Wait for simulation and robot bridge nodes to initialize
        time.sleep(10)

    @classmethod
    def tearDownClass(cls):
        """Clean up ROS 2 resources and terminate Gazebo."""
        cls.node.destroy_node()
        rclpy.shutdown()
        stop_gazebo()

    def test_odom_topic_and_movement(self, proc_output):
        """Test that odometry is published and position updates upon velocity command."""
        msgs = []

        sub = self.__class__.node.create_subscription(
            Odometry,
            "/vacuum_cleaner/odom",
            lambda msg: msgs.append(msg),
            qos_profile=10,
        )

        # Wait for initial odometry messages
        for _ in range(30):
            rclpy.spin_once(self.__class__.node, timeout_sec=0.1)
            if msgs:
                break

        self.assertGreater(
            len(msgs),
            0,
            msg="No odometry messages received on /vacuum_cleaner/odom",
        )

        # Publisher for teleoperation commands
        pub = self.__class__.node.create_publisher(
            Twist,
            "/vacuum_cleaner/cmd_vel",
            qos_profile=10,
        )

        twist_msg = Twist()
        twist_msg.linear.x = 0.5  # Move forward at 0.5 m/s
        twist_msg.angular.z = 0.2  # Turn at 0.2 rad/s

        # Publish velocity commands to move the robot
        for _ in range(25):
            pub.publish(twist_msg)
            rclpy.spin_once(self.__class__.node, timeout_sec=0.1)

        # Verify that odometry displacement occurred
        self.assertGreater(
            len(msgs),
            1,
            msg="Insufficient odometry updates received during velocity publish",
        )
        self.assertNotAlmostEqual(
            msgs[0].pose.pose.position.x,
            msgs[-1].pose.pose.position.x,
            places=3,
            msg="Roomba did not displace along x-axis upon receiving cmd_vel",
        )

        self.__class__.node.destroy_subscription(sub)
        self.__class__.node.destroy_publisher(pub)

    def test_laser_scan_topic(self, proc_output):
        """Test that the laser scan topic receives range measurements."""
        msgs = []

        sub = self.__class__.node.create_subscription(
            LaserScan,
            "/vacuum_cleaner/laser/scan",
            lambda msg: msgs.append(msg),
            qos_profile=10,
        )

        for _ in range(30):
            rclpy.spin_once(self.__class__.node, timeout_sec=0.1)
            if msgs:
                break

        self.assertGreater(
            len(msgs),
            0,
            msg="No laser scan messages received on /vacuum_cleaner/laser/scan",
        )

        self.__class__.node.destroy_subscription(sub)

    def test_bumper_topics_availability(self, proc_output):
        """Test that the center, left, and right bumper event topics exist in ROS 2 graph."""
        topic_names_and_types = dict(self.__class__.node.get_topic_names_and_types())

        bumper_topics = [
            "/vacuum_cleaner/events/center_bumper",
            "/vacuum_cleaner/events/left_bumper",
            "/vacuum_cleaner/events/right_bumper",
        ]

        for topic in bumper_topics:
            self.assertIn(
                topic,
                topic_names_and_types,
                msg=f"Bumper event topic {topic} is not published in ROS 2 graph",
            )
