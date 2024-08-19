import os
from setuptools import setup
from glob import glob

package_name = 'jderobot_drones'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'sim_config/px4_classic'), glob('sim_config/px4_classic/*')),
        (os.path.join('share', package_name, 'sim_config/gzsim'), glob('sim_config/gzsim/*'))
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='JdeRobot',
    maintainer_email='pawanw17@gmail.com',
    description='Jde Robot drones package to integrate Aerostack2 and pixhawk with Robotics Academy',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
        ],
    },
)
