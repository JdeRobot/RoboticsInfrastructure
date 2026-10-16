from setuptools import setup

package_name = "dobot_magician_bridge"

setup(
    name=package_name,
    version="0.0.1",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="aquintan",
    maintainer_email="aquintana.camacho@gmail.com",
    description="ROS2 driver that makes the real Dobot Magician look like the simulated one",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "bridge_node = dobot_magician_bridge.bridge_node:main",
        ],
    },
)
