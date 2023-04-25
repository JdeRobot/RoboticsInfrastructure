from src.manager.launcher.launcher_interface import ILauncher
from src.manager.docker_thread.docker_thread import DockerThread
from src.manager.vnc.vnc_server import Vnc_server
import time
import os
import stat

class LauncherRviz(ILauncher):
    display: str
    internal_port: str
    external_port: str
    running = False

    
    def run(self, callback):
        DRI_PATH = os.path.join("/dev/dri", os.environ.get("DRI_NAME", "card0"))
        ACCELERATION_ENABLED = self.check_device(DRI_PATH)
        rviz_vnc = Vnc_server()

        if ACCELERATION_ENABLED:
            rviz_vnc.start_vnc_gpu(self.display, self.internal_port, self.external_port, DRI_PATH)
            rviz_cmd = f"export DISPLAY=:0; export VGL_DISPLAY={DRI_PATH}; vglrun rviz2"
        else:
            rviz_vnc.start_vnc(self.display, self.internal_port, self.external_port)
            rviz_cmd = f"export DISPLAY=:0; rviz2"

        rviz_thread = DockerThread(rviz_cmd)
        rviz_thread.start()
        self.running = True

    def check_device(self, device_path):
        try:
            return stat.S_ISCHR(os.lstat(device_path)[stat.ST_MODE])
        except:
            return False

    def is_running(self):
        return self.running

    def terminate(self):
        pass

    def died(self):
        pass
