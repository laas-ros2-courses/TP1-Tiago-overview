from setuptools import find_packages, setup

package_name = 'tiago_go_to_point'

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
    maintainer='cpene',
    maintainer_email='pene.clement@gmail.com',
    description='Action GoToPoint pour TIAGo (serveur+client)',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'go_to_point_server = tiago_go_to_point.go_to_point_server:main',
            'go_to_point_client = tiago_go_to_point.go_to_point_client:main',
        ],
    },
)
