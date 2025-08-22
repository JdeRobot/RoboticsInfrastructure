"""Utility functions with common usage in tests."""


import psutil


def stop_gazebo():
    """
    Terminates any running Gazebo-related processes.

    Iterates through all running processes and terminates those whose names or cmds
    match Gazebo-related executables.
    """
    # Stop any running Gazebo processes
    for proc in psutil.process_iter(["name", "cmdline"]):
        cmdline_list = proc.info.get("cmdline")
        cmdline = " ".join(cmdline_list) if cmdline_list else ""
        if (
            proc.info["name"]
            in [
                "gzserver",
                "gazebo",
                "ign gazebo",
                "gz",
            ]
            or "gz sim" in cmdline
        ):
            print(f"Stopping Gazebo process (PID={proc.pid}, CMD={cmdline})")
            proc.terminate()
