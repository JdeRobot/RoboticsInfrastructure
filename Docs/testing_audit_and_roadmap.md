# Testing Infrastructure Audit & Roadmap Report
**Repository:** JdeRobot / RoboticsInfrastructure  
**Branch:** ROS 2 Humble (`humble-devel`)  
**Date:** October 2026  

---

## 1. Executive Summary

A comprehensive audit of the test suite, build system (`CMakeLists.txt`), CI workflows (`.github/workflows/`), launch scripts, and custom packages was conducted.

### Key Finding
**Tests are currently NOT executed in CI at all.** The entire test block inside `CustomRobots/CMakeLists.txt` was commented out with `#`. Consequently, when GitHub Actions runs `colcon test --packages-select custom_robots`, `colcon` detects **0 tests**, passes immediately with exit code 0, and gives a false sense of security (false-green CI check).

Additionally, across the 68 launch files, 57 URDFs, 81 worlds, and multiple custom Python modules, automated testing is largely missing or suffering from assertion bugs, race conditions, and skipped suites.

---

## 2. Deep Dive: Existing Tests & Identified Flaws

### Issue 1: CI Launch Tests Commented Out (Silent No-Op)
* **File:** `CustomRobots/CMakeLists.txt` (lines 139–150)
* **Description:**
  ```cmake
  if(BUILD_TESTING)
    # find_package(ament_lint_auto REQUIRED)
    # ament_lint_auto_find_test_dependencies()
    # find_package(launch_testing_ament_cmake REQUIRED)
    # file(GLOB TEST_FILES "${RI_ROOT_DIR}/test/test*.py")
    # foreach(test_file ${TEST_FILES})
    #   add_launch_test(${test_file} TIMEOUT 90)
    # endforeach()
  endif()
  ```
* **Impact:** 
  * In `.github/workflows/ros2_launch_tests.yaml`, `colcon test` executes 0 tests.
  * In `.github/workflows/ros2_gz_harmonic_launch_tests.yaml`, a `sed` command attempts to replace the test glob path, but because the enclosing block is commented out, Gazebo Harmonic tests are also never registered.

---

### Issue 2: Tests Skipped in CI Environment
* **Files:**
  * `test/test_3d_reconstruction.py` (lines 68–71, 109–112)
  * `test/test_simple_circuit.py` (lines 121–124)
* **Description:**
  ```python
  @unittest.skipIf(
      os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true",
      "Camera tests are unreliable in CI environments",
  )
  ```
* **Impact:** In `test_3d_reconstruction.py`, both existing tests (`test_camera_topics` and `test_camera_images`) are decorated with this skip condition. Therefore, the entire test file performs zero verifications in CI.

---

### Issue 3: Flawed Assertions & IndexError Bugs
* **Flawed Odometry Delta Assertion:**
  * In `test/test_simple_circuit.py` and `test/test_vacuum_cleaner.py`:
    ```python
    self.assertNotAlmostEqual(
        msgs[0].pose.pose.position.x,
        msgs[-1].pose.pose.position.x,
    )
    ```
    If only one message was received initially (`len(msgs) == 1`) and no new messages arrived during the publish loop, `msgs[0]` and `msgs[-1]` point to the exact same object. The assertion fails even if the simulation moved or conversely passes inappropriately without verifying multiple distinct samples. A length check (`assertGreater(len(msgs), 1)`) is missing.
* **IndexError Crash Before Assertion:**
  * In `test/harmonic/test_follow_road.py`:
    ```python
    self.assertNotAlmostEqual(msgs[-1].pose.position.x, msgs[0].pose.position.x)
    self.assertNotEqual(len(msgs), 0, msg="No cmd_vel messages received.")
    ```
    `msgs[-1]` is indexed before validating that `len(msgs) > 0`. If 0 messages arrive, the test crashes with an unhandled `IndexError` rather than providing an informative test failure. Furthermore, `msgs` subscribes to `/drone0/ground_truth/pose`, but the error message mistakenly states `"No cmd_vel messages received."`

---

### Issue 4: Copy-Paste Errors & Inconsistent Documentation
* **File:** `test/harmonic/test_follow_road.py`
* **Description:**
  * Header docstring: `"""Tests for the Vacuum Cleaner (no localization) ROS launch file."""`
  * Function docstring: `"""Generate the launch description for simple circuit exercise tests."""`
  * Class docstring: `"""Unit tests for verifying camera topics and images."""`
  * Line 160: `twist_msg.angular.z = 0.1 # Turn at 10 rad/s` (comment contradicts actual value: 0.1 vs 10).

---

### Issue 5: Gazebo Process Teardown Flaws
* **File:** `test/utils.py` (`stop_gazebo`)
* **Description:**
  * `psutil.process_iter` lacks exception handling for `psutil.NoSuchProcess` or `psutil.AccessDenied`.
  * `proc.terminate()` is non-blocking and does not wait (`proc.wait(timeout=...)`). When subsequent tests launch immediately, lingering Gazebo instances continue to bind ports (e.g. 11345), leading to port collision and flaky test execution.
  * Child processes spawned by Gazebo/ROS are not traversed recursively.

---

### Issue 6: Hardcoded Sleep Anti-Pattern
* **Files:**
  * `test/test_follow_person_followingcam.py` (`time.sleep(30)`)
  * `test/test_3d_reconstruction.py` (`time.sleep(10)`)
  * `test/harmonic/test_follow_road.py` (`time.sleep(15)`)
* **Impact:** Static sleeps needlessly prolong test runtime on high-performance machines while remaining vulnerable to timeouts on heavily-loaded CI runners. Polling topic discovery with timeouts should be used instead.

---

### Issue 7: Outdated ROS 1 File in ROS 2 Repository
* **File:** `CustomRobots/pick_place/pick_place_exercise/test_pick_and_place.py`
* **Description:** Contains legacy ROS 1 imports (`import rospy`, `from actionlib import ...`, `moveit_commander`) inside the ROS 2 codebase. It fails with `ModuleNotFoundError` if imported in a ROS 2 environment.

---

## 3. High-Value Missing Test Scenarios (Testing Gap Analysis)

### 1. Static / Smoke Validation for Launch Files (Highest ROI)
* **Scope:** 68 launch files in `Launchers/`.
* **Proposed Test:** An automated pytest suite that parses and evaluates `generate_launch_description()` for every `.launch.py` file to verify:
  * Python AST / syntax correctness.
  * Valid node names, package imports, and launch argument declarations.
  * Missing dependencies or broken file paths without having to start a heavy Gazebo GUI.

### 2. Robot URDF / Xacro Consistency Tests
* **Scope:** 57 URDFs in `Universes/` and Xacro definitions in `CustomRobots/`.
* **Proposed Test:** A parser test running `check_urdf` and `xacro` validation to ensure kinematics trees, link references, and XML schemas are free of syntax errors or broken tags.

### 3. Worlds and 3D Asset Path Verification
* **Scope:** 81 worlds and meshes in `Worlds/`.
* **Proposed Test:** An XML/SDF parser to inspect all `<uri>model://...</uri>` and `<uri>file://...</uri>` links, validating that every referenced 3D model, mesh (`.dae`, `.stl`, `.glb`), and texture exists in the repository tree.

### 4. Unit Tests for Core Python Packages
* **`jderobot_drones/drone_wrapper.py`:**
  * Add unit tests with mock ROS services/actions for state transitions.
  * Implement and verify timeout handling for `takeoff()` and `land()` to avoid unbounded `while True` hangs.
* **`jderobot_drones/image_sub.py`:**
  * Test graceful handling when `get_frontal_image()` or `get_ventral_image()` is requested before the first image frame arrives.
* **`utils/model_teleoperator.py`:**
  * Test websocket message parsing (`w` -> `UVF`, `s` -> `UVB`, `a` -> `UAL`, `d` -> `UAR`, `x` -> `US-`) and UDP transmission logic.
* **`CustomRobots/car_junction/scripts/TrafficSystem.py`:**
  * Unit test mathematical Euler-to-Quaternion (`etoq`) conversions.

### 5. Docker Entrypoint & GPU Acceleration Scripts
* **Scope:** `scripts/set_dri_name.sh` and `scripts/entrypoint.sh`.
* **Proposed Test:** Test vendor detection logic (NVIDIA, AMD, Intel, Microsoft WSL) using mock `lspci` and `/dev/dri` outputs.

---

## 4. Implementation Plan & Progress

- [x] **Phase 1: CI Launch Test Activation**
  - Uncomment and configure `launch_testing_ament_cmake` and `add_launch_test` in `CustomRobots/CMakeLists.txt`.
  - Ensure compatibility with both Classic Gazebo and Gazebo Harmonic GitHub Actions workflows.
- [ ] **Phase 2: Fix Flawed Test Logic & Gazebo Cleanup**
  - Refactor `test/utils.py` to reliably terminate Gazebo and child processes with timeouts and exception handling.
  - Fix indexing and assertion order in `test/harmonic/test_follow_road.py`.
  - Fix odometry delta assertions in `test_simple_circuit.py` and `test_vacuum_cleaner.py`.
  - Replace blind `time.sleep()` calls with dynamic topic discovery polling.
- [ ] **Phase 3: Add Static Launch & Asset Linters**
  - Implement pytest suite to validate all 68 `.launch.py` files.
  - Implement URDF and World mesh path integrity tests.
- [ ] **Phase 4: Python Unit Tests**
  - Add unit test suites for `drone_wrapper.py`, `model_teleoperator.py`, and `TrafficSystem.py`.
