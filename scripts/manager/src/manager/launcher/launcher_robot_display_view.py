from src.manager.manager.launcher.launcher_interface import ILauncher
from src.manager.manager.docker_thread.docker_thread import DockerThread
from src.manager.manager.vnc.vnc_server import Vnc_server
import time


class LauncherRobotDisplayView(ILauncher):
    display: str
    internal_port: str
    external_port: str
    height: int
    width: int
    running = False

    def run(self, callback):
        robot_vnc = Vnc_server()
        robot_vnc.start_vnc(self.display, self.internal_port, self.external_port)

        # Write display config and start RobotDisplayViewVNC
        robot_cmd = (f"export DISPLAY=2;")
        robot_thread = DockerThread(robot_cmd)
        robot_thread.start()

        self.running = True

    def is_running(self):
        return self.running

    def terminate(self):
        pass

    def died(self):
        pass
