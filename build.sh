#!/bin/bash

if [ $# -ne 1 ] ; then
    echo usage: ./build.sh \<tag\>
    exit 1
fi
tag=$1

sudo docker build -f scripts/Dockerfile.base -t humble_base .
sudo docker build --no-cache=true -f scripts/Dockerfile -t jderobot/robotics-academy:$tag .