from src.manager.launcher.launcher_interface import ILauncher
from src.manager.docker_thread.docker_thread import DockerThread
from src.manager.vnc.vnc_server import Vnc_server
import time
import os
import stat


class LauncherConsole(ILauncher):
    display: str
    internal_port: str
    external_port: str
    running = False

    def run(self, callback):
        DRI_PATH = os.path.join("/dev/dri", os.environ.get("DRI_NAME", "card0"))
        ACCELERATION_ENABLED = self.check_device(DRI_PATH)

        console_vnc = Vnc_server()
        
        if (ACCELERATION_ENABLED):
            console_vnc.start_vnc_gpu(self.display, self.internal_port, self.external_port,DRI_PATH)
            # Write display config and start the console
            console_cmd = f"export VGL_DISPLAY={DRI_PATH}; export DISPLAY={self.display}; vglrun xterm -fullscreen -sb -fa 'Monospace' -fs 10 -bg black -fg white"
        else:
            console_vnc.start_vnc(self.display, self.internal_port, self.external_port)
            # Write display config and start the console
            console_cmd = f"export DISPLAY={self.display};xterm -geometry 100x10+0+0 -fa 'Monospace' -fs 10 -bg black -fg white"

        console_thread = DockerThread(console_cmd)
        console_thread.start()

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
