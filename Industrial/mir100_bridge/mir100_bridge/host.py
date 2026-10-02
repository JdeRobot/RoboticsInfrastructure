import os
import socket

# Address the MiR100 has on its own wifi
DEFAULT_ROBOT_IP = "192.168.12.20"


def resolve_robot_host(configured=""):
    """Find the MiR100 itself, it defaults to the address it has on its own wifi."""
    return configured or os.environ.get("MIR100_ROBOT_IP") or DEFAULT_ROBOT_IP


def default_gateway():
    """Return the default gateway of the container, which is the docker host on Linux."""
    with open("/proc/net/route") as routes:
        for line in list(routes)[1:]:
            fields = line.split()
            if fields[1] == "00000000":
                # The kernel prints the address as little endian hex
                return socket.inet_ntoa(bytes.fromhex(fields[2])[::-1])
    return None


def resolve_ros1_host(configured=""):
    """Find the machine running the student's ROS1 side, since localhost is the container itself."""
    if configured:
        return configured

    from_env = os.environ.get("MIR100_ROS1_HOST")
    if from_env:
        return from_env

    # Docker Desktop provides this name, Linux needs an extra_hosts entry for it
    try:
        socket.gethostbyname("host.docker.internal")
        return "host.docker.internal"
    except OSError:
        pass

    try:
        gateway = default_gateway()
    except OSError:
        gateway = None
    return gateway or "localhost"
