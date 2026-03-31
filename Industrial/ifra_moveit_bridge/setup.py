from setuptools import find_packages, setup

package_name = 'ifra_moveit_bridge'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='jepear19',
    maintainer_email='jesusper2010@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'robmove_server = ifra_moveit_bridge.robmove_server:main',
            'move_server = ifra_moveit_bridge.move_server:main',
            'robpose_node = ifra_moveit_bridge.robpose_node:main',
        ],
    },
)
