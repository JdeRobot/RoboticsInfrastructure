import time
from src.manager.docker_thread.docker_thread import DockerThread


class Vnc_server:
    def start_vnc(self,display, internal_port, external_port):
        
        # Start X server in display
        xserver_cmd = f"/usr/bin/Xorg -quiet -noreset +extension GLX +extension RANDR +extension RENDER -logfile ./xdummy.log -config ./xorg.conf {display}"
        xserver_thread = DockerThread(xserver_cmd)
        xserver_thread.start()
        time.sleep(1)

        # Start VNC server without password, forever running in background
        x11vnc_cmd = f"x11vnc -quiet -display {display} -nopw -forever -xkb -bg -rfbport {internal_port}"
        x11vnc_thread = DockerThread(x11vnc_cmd)
        x11vnc_thread.start()

        # Start noVNC with default port 6080 listening to VNC server on 5900
        novnc_cmd = f"/noVNC/utils/novnc_proxy --listen {external_port} --vnc localhost:{internal_port}"
        novnc_thread = DockerThread(novnc_cmd)
        novnc_thread.start()

    def start_vnc_gpu(self,display, internal_port, external_port, dri_path):
        # Start X and VNC servers
        turbovnc_cmd = f"export VGL_DISPLAY={dri_path} && export TVNC_WM=startlxde && /opt/TurboVNC/bin/vncserver {display} -geometry '1920x1080' -vgl -noreset -SecurityTypes None -rfbport {internal_port}"
        turbovnc_thread = DockerThread(turbovnc_cmd)
        turbovnc_thread.start()
        time.sleep(1)

        # Start noVNC with default port 6080 listening to VNC server on 5900
        novnc_cmd = f"/noVNC/utils/novnc_proxy --listen {external_port} --vnc localhost:{internal_port}"
        novnc_thread = DockerThread(novnc_cmd)
        novnc_thread.start()


