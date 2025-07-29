#!/usr/bin/env python3

import os
import unittest
import pytest

import launch
import launch_testing
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


@pytest.mark.launch_test
def generate_test_description():
    # Get absolute path to the launcher
    launcher_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "Launchers",
        "3d_reconstruction.launch.py",
    )

    # Include the launcher we want to test
    launch_description = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(launcher_path),
        launch_arguments={
            "headless": "True",
            "use_simulator": "True",
            "world_file_name": "kobuki_1_reconstruction3d.world",
        }.items(),
    )

    return LaunchDescription(
        [
            launch_description,
            launch_testing.actions.ReadyToTest(),
        ]
    )


class Test3DReconstruction(unittest.TestCase):
    def test_gazebo_server_starts(self, proc_info):
        """Test that the Gazebo server process starts."""
        proc_info.assertThat(
            "gzserver",
            launch_testing.asserts.processes.ProcessStarts(timeout=90),
        )

    def test_world_loads(self, proc_output):
        """Test that the world loads correctly."""
        proc_output.assertWaitFor("Loading world", process="gzserver", timeout=90)
