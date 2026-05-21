import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/hannah/Workspace/ros2_ws/install/ros2_sumo'
