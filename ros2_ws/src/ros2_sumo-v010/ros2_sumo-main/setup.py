import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'ros2_sumo'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
        (os.path.join('share', package_name, 'config'), glob(os.path.join('config', '*.rviz'))),
        (os.path.join('share', package_name, 'scenarios'), glob(os.path.join('scenarios', '*.*')))
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Marc Rene Zofka',
    maintainer_email='marc-rene.zofka@hs-heilbronn.de',
    description='ROS2 Wrapper for SUMO',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
             'traffic_lights_publisher = ros2_sumo.traffic_lights_publisher:main',
             'vehicle_publisher = ros2_sumo.vehicle_publisher:main',
             'multi_sim_publisher = ros2_sumo.multi_sim_publisher:main',
             'arduino_read_write = ros2_sumo.arduino_read_write:main',
        ],
    },
)
