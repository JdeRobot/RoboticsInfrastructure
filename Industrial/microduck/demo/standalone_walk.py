#!/usr/bin/env python3
"""Stand-alone MuJoCo sim of microduck walking in passive mode."""

import os
import time

import mujoco
import mujoco.viewer

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mujoco")
SCENE_PATH = os.path.join(MODEL_DIR, "scene_walk.xml")


def main():
    model = mujoco.MjModel.from_xml_path(SCENE_PATH)
    data = mujoco.MjData(model)
    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            mujoco.mj_step(model, data)
            viewer.sync()
            time.sleep(model.opt.timestep)


if __name__ == "__main__":
    main()
