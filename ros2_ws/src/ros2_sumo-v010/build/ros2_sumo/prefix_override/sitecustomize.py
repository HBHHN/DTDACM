import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/hannah/Workspace/ros2_ws/src/ros2_sumo-v010/install/ros2_sumo'
