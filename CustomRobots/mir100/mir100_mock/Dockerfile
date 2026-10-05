FROM ros:noetic-ros-base

RUN apt-get update && apt-get install -y --no-install-recommends \
        git build-essential python3-catkin-tools python3-rosdep \
        ros-noetic-rosbridge-server \
        python3-numpy \
    && rm -rf /var/lib/apt/lists/*

# Same driver the customer builds from source
RUN mkdir -p /ws/src && git clone --depth 1 -b noetic https://github.com/DFKI-NI/mir_robot.git /ws/src/mir_robot
RUN apt-get update && cd /ws \
    && rosdep install --from-paths src/mir_robot/mir_driver src/mir_robot/mir_msgs src/mir_robot/mir_actions \
        src/mir_robot/sdc21x0 src/mir_robot/mir_description --ignore-src -r -y \
    && rm -rf /var/lib/apt/lists/*
RUN cd /ws && . /opt/ros/noetic/setup.sh \
    && catkin_make -DCATKIN_WHITELIST_PACKAGES="mir_driver;mir_msgs;mir_actions;sdc21x0;mir_description"

COPY fake_mir.py start_fake_mir.sh start_mir_driver.sh /mock/
RUN chmod +x /mock/fake_mir.py /mock/start_fake_mir.sh /mock/start_mir_driver.sh

ENTRYPOINT ["/ros_entrypoint.sh"]
