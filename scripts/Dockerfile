FROM humble_base

# RAM and src directory
COPY ./scripts/manager/src /src
COPY ./scripts/manager/src/manager/manager.py /

# copy scripts for vnc displays
COPY ./scripts/start_vnc.sh /
COPY ./scripts/kill_all.sh /
COPY ./scripts/entrypoint.sh /

# give execution permissions
RUN chmod +x /start_vnc.sh /kill_all.sh /entrypoint.sh /manager.py

# environment
COPY ./.env /.env

# configure bashrc
RUN echo 'export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:/home/ws/src/amazon_hospital/models' >> ~/.bashrc
RUN echo 'export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:/home/ws/src/amazon_hospital/fuel_models' >> ~/.bashrc
RUN echo 'export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:/home/ws/src/amazon_hospital/hospital_world/models' >> ~/.bashrc
RUN echo 'export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:/home/ws/install/custom_robots/share' >> ~/.bashrc
RUN echo 'source /usr/share/gazebo/setup.bash' >> ~/.bashrc

# RoboticsAcademy
COPY ./RoboticsAcademy /RoboticsAcademy
# Custom Robot Repository
RUN mkdir -p /opt/jderobots 
COPY ./CustomRobots /opt/jderobots/CustomRobots

# create workspace and add Robot packages
RUN mkdir -p /home/ws/src
RUN cp -r /opt/jderobots/CustomRobots /home/ws/src/

# Compile workspace
WORKDIR /home/ws
RUN sudo rosdep fix-permissions && rosdep update
RUN rosdep install --from-paths src --ignore-src -r --rosdistro humble -y
RUN colcon build --symlink-install

# Django server
EXPOSE 8000
# Manager websocket
EXPOSE 7163

# Exercise websocket
EXPOSE 1905
# GUI websockets
EXPOSE 2303

# noVNC Console
EXPOSE 1108
# noVNC Gazebo
EXPOSE 6080
# noVNC Rviz
EXPOSE 6081
# noVNC GUI
EXPOSE 6082

# WebRtc
EXPOSE 1831

WORKDIR /
CMD ["./entrypoint.sh"]