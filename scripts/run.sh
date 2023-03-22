#!/bin/bash

volume=false
name=dockerRam_container
unset route
unset debug

while [[ "$1" =~ ^- && ! "$1" == "--" ]]; do case $1 in
    -v | --volume )
        shift;
        route=$1
        volume=true
        ;;
    -n | --name )
        shift; 
        name=$1
        ;;
    -d | --debug )
        shift; 
        debug=bash
        ;;
esac; shift; done
if [[ "$1" == '--' ]]; then shift; fi

if [ -z $name ]; then
    name=dockerRam_container
    echo name not specified, container name will be: dockerRam_container
fi

if $volume && [ ! -z $route ] && [ -d $route ] ; then
    docker run --name $name -v $route:/home/shared_dir --rm -it -p 2303:2303 -p 1905:1905 -p 8765:8765 -p 6080:6080 -p 6081:6081 -p 1108:1108 -p 6082:6082 -p 7163:7163 jderobot/robotics-academy:4.3.0 $debug
else
    docker run --name $name --rm -it -p 2303:2303 -p 1905:1905 -p 8765:8765 -p 6080:6080 -p 6081:6081 -p 1108:1108 -p 6082:6082 -p 7163:7163 jderobot/robotics-academy:4.3.0 $debug
fi