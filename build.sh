#!/bin/bash

sudo docker build -f scripts/Dockerfile.base -t humble_base .
sudo docker build --no-cache=true -f scripts/Dockerfile -t jderobot/robotics-academy:4.3.0 .