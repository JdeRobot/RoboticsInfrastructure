#!/bin/bash

usage() {
    echo 'usage: /start_vnc.sh <display> <internal_port> <external_port> 
        example: >> /start_vnc.sh 0 5900 6080'
}

if [ $# -ne 3 ] ; then
    usage
    exit 1
fi


cd /
## xserver:
/usr/bin/Xorg -noreset -quiet +extension GLX +extension RANDR +extension RENDER -logfile ./xdummy.log -config ./xorg.conf :$1 &
sleep 1
## lanzar servidor vnc
x11vnc -display :$1 -quiet -nopw -forever -xkb -bg -rfbport $2 &
sleep 1
## lanzar cliente noVNC
/noVNC/utils/novnc_proxy --listen $3 --vnc localhost:$2 &