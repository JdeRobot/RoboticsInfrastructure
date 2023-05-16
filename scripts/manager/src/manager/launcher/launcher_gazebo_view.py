from src.manager.manager.launcher.launcher_interface import ILauncher
from src.manager.manager.docker_thread.docker_thread import DockerThread
from src.manager.manager.vnc.vnc_server import Vnc_server
import time
import os
import stat


class LauncherGazeboView(ILauncher):
    exercise_id: str
    display: str
    internal_port: str
    external_port: str
    height: int
    width: int
    running = False
    threads = []

    def run(self, callback):
        DRI_PATH = os.path.join(
            "/dev/dri", os.environ.get("DRI_NAME", "card0"))
        ACCELERATION_ENABLED = self.check_device(DRI_PATH)

        # Configure browser screen width and height for gzclient
        gzclient_config_cmds = f"echo [geometry] > ~/.gazebo/gui.ini; echo x=0 >> ~/.gazebo/gui.ini; echo y=0 >> ~/.gazebo/gui.ini; echo width={self.width} >> ~/.gazebo/gui.ini; echo height={self.height} >> ~/.gazebo/gui.ini;"
        gz_vnc = Vnc_server()

        if ACCELERATION_ENABLED:
            gz_vnc.start_vnc_gpu(self.display, self.internal_port, self.external_port, DRI_PATH)
            # Write display config and start gzclient
            gzclient_cmd = (
                f"export DISPLAY=:0; {gzclient_config_cmds} export VGL_DISPLAY={DRI_PATH}; vglrun gzclient --verbose")
        else:
            gz_vnc.start_vnc(self.display, self.internal_port, self.external_port)
            # Write display config and start gzclient
            gzclient_cmd = (
                f"export DISPLAY=:0; {gzclient_config_cmds} gzclient --verbose")

        # wait for vnc and gazebo servers to load properly
        if (self.exercise_id == "follow_person_newmanager"):
            time.sleep(6)
        else:
            time.sleep(0.1)

        gzclient_thread = DockerThread(gzclient_cmd)
        gzclient_thread.start()
        self.threads.append(gzclient_thread)

        self.running = True

    def check_device(self, device_path):
        try:
            return stat.S_ISCHR(os.lstat(device_path)[stat.ST_MODE])
        except:
            return False

    def is_running(self):
        return self.running

    def terminate(self):
        for thread in self.threads:
            thread.terminate()
            thread.join()
        self.running = False

    def died(self):
        pass
