#!/bin/bash

sudo docker build -f Dockerfile.base -t humble_base .
sudo docker build --no-cache=true -f Dockerfile.turtlebot2 -t turtlebot2 .