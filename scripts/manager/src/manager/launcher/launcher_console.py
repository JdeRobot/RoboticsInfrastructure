from src.manager.launcher.launcher_interface import ILauncher
from src.manager.docker_thread.docker_thread import DockerThread
from src.manager.vnc.vnc_server import Vnc_server
import time


class LauncherConsole(ILauncher):
    display: str
    internal_port: str
    external_port: str
    running = False

    def run(self, callback):
        console_vnc = Vnc_server()
        console_vnc.start_vnc(self.display, self.internal_port, self.external_port)

        # Write display config and start the console
        console_cmd = f"export DISPLAY={self.display};xterm -geometry 100x10+0+0 -fa 'Monospace' -fs 10 -bg black -fg white"
        console_thread = DockerThread(console_cmd)
        console_thread.start()

        self.running = True

    def is_running(self):
        return self.running

    def terminate(self):
        pass

    def died(self):
        pass
