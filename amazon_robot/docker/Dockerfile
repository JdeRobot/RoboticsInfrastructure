FROM rosplanning/navigation2:main.release

# Change to Cyclone dds
#
#RUN apt-get update && apt-get install -q -y \
#    ros-foxy-rmw-cyclonedds-cpp\
#    && rm -rf /var/lib/apt/lists/*

#ARG RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

#RUN /bin/bash -c  "source /opt/ros/foxy/setup.sh  ros2 doctor --report"
WORKDIR /opt/overlay_ws/

# For SLAM toolbox
RUN  /bin/bash -c "cd /opt/overlay_ws/src && git clone -b foxy-devel https://github.com/SteveMacenski/slam_toolbox.git"

RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends apt-utils

RUN . /opt/underlay_ws/install/setup.sh \
    && cd /opt/overlay_ws/ \
    && rosdep update \
    && rosdep install -y -r --from-paths src --ignore-src --rosdistro=foxy -y



RUN . /opt/underlay_ws/install/setup.sh && \
    colcon build \
      --symlink-install \
      --mixin $OVERLAY_MIXINS \
    || ([ -z "$FAIL_ON_BUILD_FAILURE" ] || exit 1)



#RUN /bin/bash -c "cd /opt/overlay_ws/ && colcon build --symlink-install"

COPY . /opt/warehouse_ws/src/

WORKDIR /opt/warehouse_ws/
#
#RUN . /opt/overlay_ws/install/setup.sh \
#    && cd /opt/overlay_ws/ \
#    && rosdep update \
#    && rosdep install -y -r --from-paths src --ignore-src --rosdistro=foxy -y
#

RUN . /opt/overlay_ws/install/setup.sh && \
    colcon build \
      --symlink-install \
    || ([ -z "$FAIL_ON_BUILD_FAILURE" ] || exit 1)

#RUN /bin/bash -c "source /opt/overlay_ws/install/setup.sh && cd /opt/warehouse_ws/ && colcon build --symlink-install"


# nvidia-container-runtime
ENV NVIDIA_VISIBLE_DEVICES \
    ${NVIDIA_VISIBLE_DEVICES:-all}
ENV NVIDIA_DRIVER_CAPABILITIES \
    ${NVIDIA_DRIVER_CAPABILITIES:+$NVIDIA_DRIVER_CAPABILITIES,}graphics


COPY docker/ros_entrypoint.sh /

ENV GAZEBO_MODEL_PATH=/opt/warehouse_ws/src/amazon_robot_gazebo/models

RUN chmod 755 /ros_entrypoint.sh

ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]


