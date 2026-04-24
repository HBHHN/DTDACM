from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    image_path = LaunchConfiguration('image_path')
    return LaunchDescription([
        Node(
            package='image_publisher',
            namespace='image_publisher',
            executable='image_publisher_node',
            name='sim',
            arguments=[image_path]
        ),
        Node(
            package='rqt_image_view',
            namespace='rqt_image_view',
            executable='rqt_image_view',
            name='sim'
        ),
        Node(
            package='image_converter',
            executable='image_converter_pkg',
            name='image_converter',
        )
    ])

