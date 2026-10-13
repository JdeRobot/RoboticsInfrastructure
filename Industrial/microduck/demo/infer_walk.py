#!/usr/bin/env python3
"""Run an ONNX walking policy on microduck if available."""

import os
import sys

# Look for onnx
DEMO_DIR = os.path.dirname(__file__)
ONNX_DIR = os.path.join(os.path.dirname(DEMO_DIR), "onnx")
MODEL_DIR = os.path.join(os.path.dirname(DEMO_DIR), "mujoco")
SCENE_PATH = os.path.join(MODEL_DIR, "scene_walk.xml")

if __name__ == "__main__":
    print("Scene:", SCENE_PATH)
    print("ONNX dir:", ONNX_DIR)
    print("Put exported .onnx in Industrial/microduck/onnx/")
