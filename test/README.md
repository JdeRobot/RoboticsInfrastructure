## Testing Launch Files

### Local Setup

-   create a virtual environment:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
-   install dependencies:

    ```bash
      pip install -r test/requirements.txt
    ```

-   source the ROS 2 environment:

    ```bash
    source /opt/ros/humble/setup.bash
    ```

-   build the workspace:

    ```bash
    colcon build --symlink-install
    ```

-   source the Gazebo environment (if applicable):

    ```bash
    source /usr/share/gazebo/setup.sh
    ```

-   source the workspace:
    ```bash
    source install/setup.bash
    ```

### Running Tests

-   run tests

    ```bash
    colcon test --event-handlers console_cohesion+ --retest-until-fail 5
    ```

-   check test results
    ```bash
    colcon test-result --verbose
    ```

### Adding New Tests

-   create a new test file in the `test` directory, e.g., `test/test_new_feature.py`

-   ensure the test file follows the naming convention `test_*.py` to be automatically discovered

-   implement the test using `launch_testing` and `pytest` as shown in existing test files

-   rebuild the workspace:

    ```bash
    colcon build --symlink-install
    ```

-   run the tests again to include the new test:

    ```bash
    colcon test --event-handlers console_direct+ --retest-until-fail 5
    ```

-   check the results to ensure the new test is included:
    ```bash
    colcon test-result --verbose
    ```

### Example Test File Structure (TBD)
