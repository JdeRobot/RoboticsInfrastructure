"""Robotiq 2F gripper over the URCap socket or over Modbus RTU.

Both give the same register level view, a position from 0 (open) to 255
(closed), and an object status that tells when the fingers stopped.
"""

import os
import socket
import struct
import termios
import time

# gOBJ values
MOVING = 0
STOPPED_OPENING = 1
STOPPED_CLOSING = 2
AT_POSITION = 3

URCAP_PORT = 63352

RTU_SLAVE = 0x09
RTU_OUTPUT = 0x03E8
RTU_INPUT = 0x07D0


class UrcapGripper:
    """Robotiq URCap socket server running on the robot controller, CB3 and e-Series."""

    def __init__(self, host, port=URCAP_PORT, timeout=2.0):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.where = f"URCap socket {host}:{port}"

    def close(self):
        self.sock.close()

    def command(self, line):
        self.sock.sendall((line + "\n").encode())
        reply = b""
        while not reply.endswith(b"\n"):
            chunk = self.sock.recv(1024)
            if not chunk:
                raise OSError("Robotiq URCap closed the connection")
            reply += chunk
        return reply.decode().strip()

    def get(self, var):
        reply = self.command(f"GET {var}")
        name, _, value = reply.partition(" ")
        if name != var:
            raise OSError(f"unexpected Robotiq reply {reply!r}")
        return int(value)

    def set(self, **values):
        args = " ".join(f"{k} {v}" for k, v in values.items())
        if self.command(f"SET {args}") != "ack":
            raise OSError(f"Robotiq rejected SET {args}")

    def status(self):
        return self.get("POS"), self.get("OBJ"), self.get("FLT")

    def active(self):
        return self.get("STA") == 3

    def activate(self):
        self.set(ACT=1)

    def reset(self):
        self.set(ACT=0)

    def move(self, position, speed, force):
        self.set(POS=position, SPE=speed, FOR=force, GTO=1)


def crc16(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return struct.pack("<H", crc)


class RtuGripper:
    """Modbus RTU on a serial port, the e-Series tool flange or a USB adapter."""

    def __init__(self, path, timeout=1.0):
        self.fd = os.open(path, os.O_RDWR | os.O_NOCTTY)
        attrs = termios.tcgetattr(self.fd)
        attrs[0] = 0
        attrs[1] = 0
        attrs[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
        attrs[3] = 0
        attrs[4] = attrs[5] = termios.B115200
        attrs[6][termios.VMIN] = 0
        attrs[6][termios.VTIME] = 1
        termios.tcsetattr(self.fd, termios.TCSANOW, attrs)
        termios.tcflush(self.fd, termios.TCIOFLUSH)
        self.timeout = timeout
        self.where = f"Modbus RTU on {path}"

    def close(self):
        os.close(self.fd)

    def transaction(self, frame, reply_size):
        frame += crc16(frame)
        termios.tcflush(self.fd, termios.TCIFLUSH)
        os.write(self.fd, frame)
        reply = b""
        deadline = time.monotonic() + self.timeout
        while len(reply) < reply_size and time.monotonic() < deadline:
            reply += os.read(self.fd, reply_size - len(reply))
        if len(reply) < reply_size or crc16(reply[:-2]) != reply[-2:]:
            raise OSError("no valid answer from the Robotiq gripper")
        return reply

    def write(self, request):
        frame = struct.pack(">BBHHB", RTU_SLAVE, 0x10, RTU_OUTPUT, 3, 6) + bytes(request)
        self.transaction(frame, 8)

    def read(self):
        frame = struct.pack(">BBHH", RTU_SLAVE, 0x04, RTU_INPUT, 3)
        return self.transaction(frame, 11)[3:9]

    def status(self):
        registers = self.read()
        return registers[4], registers[0] >> 6, registers[2] & 0x0F

    def active(self):
        return (self.read()[0] >> 4) & 0x03 == 3

    def activate(self):
        self.write([0x01, 0, 0, 0, 0, 0])

    def reset(self):
        self.write([0, 0, 0, 0, 0, 0])

    def move(self, position, speed, force):
        self.write([0x09, 0, 0, position, speed, force])
