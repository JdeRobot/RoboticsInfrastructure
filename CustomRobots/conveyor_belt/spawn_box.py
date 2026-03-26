#!/usr/bin/env python3

import subprocess
import time

i = 0

while True:
    name = f"box_{i}"

    cmd = [
        "ros2", "run", "ros_gz_sim", "create",
        "-name", name,
        "-x", "0.0",
        "-y", "0.0",
        "-z", "1.0",
        "-file", "model://box"
    ]

    subprocess.run(cmd)
    print(f"Spawned {name}")

    i += 1
    time.sleep(2)