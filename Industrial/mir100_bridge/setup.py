from setuptools import setup

package_name = "mir100_bridge"

setup(
    name=package_name,
    version="0.0.1",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools", "roslibpy"],
    zip_safe=True,
    maintainer="aquintan",
    maintainer_email="aquintana.camacho@gmail.com",
    description="ROS1 to ROS2 bridge node for the real/mocked MiR100",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "bridge_node = mir100_bridge.bridge_node:main",
        ],
    },
)
