#!/usr/bin/env python3
"""Simple MuJoCo viewer test for microduck."""

import os
import sys

import mujoco
import mujoco.viewer

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mujoco")
SCENE_PATH = os.path.join(MODEL_DIR, "scene_walk.xml")


def main():
    if not os.path.exists(SCENE_PATH):
        print(f"Model not found: {SCENE_PATH}", file=sys.stderr)
        sys.exit(1)
    model = mujoco.MjModel.from_xml_path(SCENE_PATH)
    data = mujoco.MjData(model)
    with mujoco.viewer.launch_passive(model, data) as viewer:
        print("Press Ctrl+C to exit")
        while viewer.is_running():
            mujoco.mj_step(model, data)
            viewer.sync()
            import time

            time.sleep(0.002)


if __name__ == "__main__":
    main()
