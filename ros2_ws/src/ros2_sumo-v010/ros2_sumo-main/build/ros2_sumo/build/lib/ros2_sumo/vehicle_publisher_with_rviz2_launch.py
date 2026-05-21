from launch import LaunchDescription
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory

base_path=os.path.realpath(get_package_share_directory('ros2_sumo'))
rviz_path=base_path+'/config/vehicle_publisher_rviz_config.rviz'

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='ros2_sumo',
            namespace='sumo',
            executable='vehicle_publisher',
            name='vehicle_publisher',
            output='screen',
            arguments=['--ros-args'],
            parameters=[{
                "delta_t":0.1,
                "delay_ms":300,
                "path":"/home/hannah/Workspace/ros2_ws/src/ros2_sumo-v010/ros2_sumo-main/scenarios/TechCampus/techcampus.sumocfg"}]
        ),
        Node(
            package='rviz2',
            namespace='sumo',
            executable='rviz2',
            name='rviz',
            arguments=['-d'+str(rviz_path)]
        )
    ])
