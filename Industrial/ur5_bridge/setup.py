from setuptools import setup

package_name = "ur5_bridge"

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
    description="Robotiq gripper and status nodes that complete the real UR5 so it looks like the simulated one",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "gripper_node = ur5_bridge.gripper_node:main",
            "status_node = ur5_bridge.status_node:main",
        ],
    },
)
