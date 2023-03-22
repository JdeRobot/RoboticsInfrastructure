from src.manager.launcher.launcher_interface import ILauncher
from src.manager.docker_thread.docker_thread import DockerThread
from src.manager.vnc.vnc_server import Vnc_server
import time


class LauncherGazeboView(ILauncher):
    display: str
    internal_port: str
    external_port: str
    height: int
    width: int
    running = False

    def run(self, callback):
        gz_vnc = Vnc_server()
        gz_vnc.start_vnc(self.display, self.internal_port, self.external_port)

        # Configure browser screen width and height for gzclient
        gzclient_config_cmds = f"echo [geometry] > ~/.gazebo/gui.ini; echo x=0 >> ~/.gazebo/gui.ini; echo y=0 >> ~/.gazebo/gui.ini; echo width={self.width} >> ~/.gazebo/gui.ini; echo height={self.height} >> ~/.gazebo/gui.ini;"
        time.sleep(0.1)
        # Write display config and start gzclient
        gzclient_cmd = (
            f"export DISPLAY=:0;  {gzclient_config_cmds} gzclient --verbose")
        gzclient_thread = DockerThread(gzclient_cmd)
        gzclient_thread.start()
        self.running = True

    def is_running(self):
        return self.running

    def terminate(self):
        pass

    def died(self):
        pass
