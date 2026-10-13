"""Dobot Magician serial protocol over plain termios.

The RADI image ships an unrelated PyPI package called serial that shadows pyserial.
"""

import glob
import os
import select
import struct
import termios
import threading
import time

# Command ids from the Dobot Communication Protocol
ID_DEVICE_TIME = 4
ID_POSE = 10
ID_ALARMS = 20
ID_HOME_CMD = 31
ID_SUCTION_CUP = 62
ID_PTP_JOINT_PARAMS = 80
ID_PTP_COMMON_PARAMS = 83
ID_PTP_CMD = 84
ID_QUEUE_START = 240
ID_QUEUE_FORCE_STOP = 242
ID_QUEUE_CLEAR = 245
ID_QUEUE_INDEX = 246

PTP_MOVJ_ANGLE = 4

# USB serial chips the Dobot Magician ships with
USB_IDS = {("10c4", "ea60"), ("1a86", "7523")}

# The container mounts the host /dev at /host_dev
DEVICE_DIRS = ["/dev", "/host_dev"]


def find_port():
    """Return the device path of the first connected Dobot, or None."""
    for tty in sorted(
        glob.glob("/sys/class/tty/ttyUSB*") + glob.glob("/sys/class/tty/ttyACM*")
    ):
        device = os.path.realpath(os.path.join(tty, "device"))
        while device != "/" and not os.path.isfile(os.path.join(device, "idVendor")):
            device = os.path.dirname(device)
        try:
            with open(os.path.join(device, "idVendor")) as f:
                vendor = f.read().strip()
            with open(os.path.join(device, "idProduct")) as f:
                product = f.read().strip()
        except OSError:
            continue
        if (vendor, product) not in USB_IDS:
            continue
        for directory in DEVICE_DIRS:
            path = os.path.join(directory, os.path.basename(tty))
            if os.path.exists(path):
                return path
    return None


class SerialPort:
    """Raw 115200 8N1 serial port."""

    def __init__(self, path):
        self.fd = os.open(path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        attrs = termios.tcgetattr(self.fd)
        attrs[0] = 0
        attrs[1] = 0
        attrs[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
        attrs[3] = 0
        attrs[4] = termios.B115200
        attrs[5] = termios.B115200
        attrs[6][termios.VMIN] = 0
        attrs[6][termios.VTIME] = 0
        termios.tcsetattr(self.fd, termios.TCSANOW, attrs)
        termios.tcflush(self.fd, termios.TCIOFLUSH)

    def write(self, data):
        os.write(self.fd, data)

    def read(self, size, timeout):
        data = b""
        deadline = time.time() + timeout
        while len(data) < size:
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            ready, _, _ = select.select([self.fd], [], [], remaining)
            if ready:
                chunk = os.read(self.fd, size - len(data))
                if not chunk:
                    raise OSError("serial port closed")
                data += chunk
        return data

    def flush_input(self):
        termios.tcflush(self.fd, termios.TCIFLUSH)

    def close(self):
        os.close(self.fd)


class Dobot:
    """Thread safe request and response commands."""

    def __init__(self, path):
        self.port = SerialPort(path)
        self.lock = threading.Lock()

    def close(self):
        self.port.close()

    def request(self, cmd_id, rw=False, queued=False, params=b""):
        control = (1 if rw else 0) | (2 if queued else 0)
        payload = bytes([cmd_id, control]) + params
        checksum = (256 - sum(payload) % 256) % 256
        frame = b"\xaa\xaa" + bytes([len(payload)]) + payload + bytes([checksum])
        with self.lock:
            self.port.flush_input()
            self.port.write(frame)
            return self.read_response(cmd_id)

    def read_response(self, cmd_id):
        deadline = time.time() + 1.0
        while time.time() < deadline:
            # Resync on the 0xAA 0xAA header
            if self.port.read(1, 0.5) != b"\xaa" or self.port.read(1, 0.5) != b"\xaa":
                continue
            length = self.port.read(1, 0.5)
            if not length:
                return None
            payload = self.port.read(length[0], 0.5)
            checksum = self.port.read(1, 0.5)
            if len(payload) != length[0] or not checksum:
                return None
            if (sum(payload) + checksum[0]) % 256 != 0 or payload[0] != cmd_id:
                continue
            return payload[2:]
        return None

    @staticmethod
    def queued_index(data):
        if data is None or len(data) < 8:
            return None
        return struct.unpack("<Q", data[:8])[0]

    def device_time(self):
        """Milliseconds since the robot was powered on."""
        data = self.request(ID_DEVICE_TIME)
        return (
            struct.unpack("<I", data[:4])[0]
            if data is not None and len(data) >= 4
            else None
        )

    def pose(self):
        """Cartesian pose followed by the four joints in firmware degrees."""
        data = self.request(ID_POSE)
        if data is None or len(data) < 32:
            return None
        return struct.unpack("<8f", data[:32])

    def alarms(self):
        data = self.request(ID_ALARMS)
        if data is None:
            return None
        return [
            i * 8 + bit
            for i, byte in enumerate(data)
            for bit in range(8)
            if byte >> bit & 1
        ]

    def clear_alarms(self):
        self.request(ID_ALARMS, rw=True)

    def start_queue(self):
        self.request(ID_QUEUE_CLEAR, rw=True)
        self.request(ID_QUEUE_START, rw=True)

    def force_stop(self):
        self.request(ID_QUEUE_FORCE_STOP, rw=True)
        self.request(ID_QUEUE_CLEAR, rw=True)
        self.request(ID_QUEUE_START, rw=True)

    def queue_index(self):
        return self.queued_index(self.request(ID_QUEUE_INDEX))

    def home(self):
        return self.queued_index(
            self.request(ID_HOME_CMD, rw=True, queued=True, params=struct.pack("<I", 0))
        )

    def set_speed(self, velocity, acceleration):
        """Same joint speed in degrees per second for the four joints."""
        params = struct.pack("<8f", *([velocity] * 4 + [acceleration] * 4))
        self.request(ID_PTP_JOINT_PARAMS, rw=True, params=params)
        self.request(ID_PTP_COMMON_PARAMS, rw=True, params=struct.pack("<2f", 100, 100))

    def move_joints(self, j1, j2, j3, j4):
        """Queue a joint space move in firmware degrees and return its queue index."""
        params = struct.pack("<Bffff", PTP_MOVJ_ANGLE, j1, j2, j3, j4)
        return self.queued_index(
            self.request(ID_PTP_CMD, rw=True, queued=True, params=params)
        )

    def suction_cup(self, on):
        self.request(ID_SUCTION_CUP, rw=True, params=bytes([int(on), int(on)]))

    def wait_queue(self, index, timeout, cancelled=lambda: False):
        """Wait until the queue reaches index and the joints stop, False on timeout or cancel."""
        start = time.time()
        reached = index is None
        last, still_since = None, None
        while time.time() - start < timeout:
            if cancelled():
                return False
            # The index moves on when a command starts so the pose has to settle too
            if not reached:
                current = self.queue_index()
                reached = current is not None and current >= index
            pose = self.pose()
            if pose is not None and last is not None:
                if max(abs(a - b) for a, b in zip(pose[4:], last[4:])) > 0.05:
                    still_since = None
                elif still_since is None:
                    still_since = time.time()
            last = pose
            if reached and still_since is not None and time.time() - still_since > 0.3:
                return True
            time.sleep(0.05)
        return False
