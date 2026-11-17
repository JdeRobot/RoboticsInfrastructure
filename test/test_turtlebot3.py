#!/usr/bin/env python3

"""Launch tests for TurtleBot3 modular robot."""

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
from sensor_msgs.msg import LaserScan, Imu
from geometry_msgs.msg import Twist

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from utils import stop_gazebo  # noqa: E402


@pytest.mark.launch_test
def generate_test_description():
    """Generate the launch description for TurtleBot3 robot tests."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Path to TurtleBot3 Burger launcher
    turtlebot_launcher_path = os.path.join(
        repo_root,
        "CustomRobots",
        "turtlebot3",
        "launch",
        "turtlebot3_burger.launch.py",
    )

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

    # Launch TurtleBot3 Burger in the turtlebot3 namespace
    turtlebot_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(turtlebot_launcher_path),
        launch_arguments={
            "use_sim_time": "true",
            "namespace": "turtlebot3",
            "entity": "turtlebot3_burger",
            "sensor": "laser",
        }.items(),
    )

    # Add model resource paths
    models_path = os.path.join(repo_root, "CustomRobots", "turtlebot3", "models")
    set_env_res = SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", models_path)
    append_env_res = AppendEnvironmentVariable("GZ_SIM_RESOURCE_PATH", models_path)

    return LaunchDescription(
        [
            set_env_res,
            append_env_res,
            gazebo_server,
            turtlebot_cmd,
            launch_testing.actions.ReadyToTest(),
        ]
    )


class TestTurtleBot3(unittest.TestCase):
    """Unit tests for verifying TurtleBot3 topics, sensors, and teleoperation."""

    @classmethod
    def setUpClass(cls):
        """Set up ROS 2 node for testing."""
        rclpy.init()
        cls.node = rclpy.create_node("test_turtlebot3_node")

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
            "/turtlebot3/odom",
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
            msg="No odometry messages received on /turtlebot3/odom",
        )

        # Publisher for teleoperation commands
        pub = self.__class__.node.create_publisher(
            Twist,
            "/turtlebot3/cmd_vel",
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
            msg="TurtleBot3 did not displace along x-axis upon receiving cmd_vel",
        )

        self.__class__.node.destroy_subscription(sub)
        self.__class__.node.destroy_publisher(pub)

    def test_laser_scan_topic(self, proc_output):
        """Test that the LDS laser scan topic receives range measurements."""
        msgs = []

        sub = self.__class__.node.create_subscription(
            LaserScan,
            "/turtlebot3/laser/scan",
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
            msg="No laser scan messages received on /turtlebot3/laser/scan",
        )

        self.__class__.node.destroy_subscription(sub)

    def test_imu_topic(self, proc_output):
        """Test that the IMU topic publishes active sensor readings."""
        msgs = []

        sub = self.__class__.node.create_subscription(
            Imu,
            "/turtlebot3/imu",
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
            msg="No IMU messages received on /turtlebot3/imu",
        )

        self.__class__.node.destroy_subscription(sub)
