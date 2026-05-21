#!/usr/bin/env python3

##################################################
#  Copyright (c) 2026, Marc Rene Zofka,
#  University of Applied Sciences, Heilbronn
#  All rights reserved.
#
#  Vehicle Publisher node.
#
#  Usage: ros2 run ros2_sumo vehicle_publisher.py --ros-args -p delta_t:=0.1 -p path:="/<path>/techcampus.sumocfg"
##################################################

__author__ = "Marc Rene Zofka"
__email__ = "marc-rene.zofka@hs-heilbronn.de"

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter

from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped

import numpy as np

import math
import os
import sys

if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

import traci
import traci.constants as tc

def quat_from_euler(ai, aj, ak):
    ai /= 2.0
    aj /= 2.0
    ak /= 2.0
    ci = math.cos(ai)
    si = math.sin(ai)
    cj = math.cos(aj)
    sj = math.sin(aj)
    ck = math.cos(ak)
    sk = math.sin(ak)
    cc = ci*ck
    cs = ci*sk
    sc = si*ck
    ss = si*sk

    q = np.empty((4, ))
    q[0] = cj*sc - sj*cs
    q[1] = cj*ss + sj*cc
    q[2] = cj*cs - sj*sc
    q[3] = cj*cc + sj*ss

    return q


class VehiclePublisher(Node):
    """
    The VehiclePublisher nodes serves as a publishing node. 
    The poses of the vehicles as well as other quantities are subscribed to be 
    published as ros2 transforms and/or topics. 
    In order to restrict the amount of restricted vehicles, a certain poi_id and 
    range is to be given to the node, which only delivers vehicles inside the 
    observation radius. 
    This node is based on a timer to be triggered at a fixed frame rate. 
    """
    def __init__(self):
        # Call ros2 node's init function
        super().__init__('vehicle_publisher')

        # Declare ros2 parameters for this node.
        self.declare_parameter('delta_t', 0.1)
        self.declare_parameter('range_m', 500.0)
        self.declare_parameter('delay_ms', 1000)
        self.declare_parameter('path', "/home/user/*.sumocfg")
        self.declare_parameter('poi_id', "label")

        # Read out ros2 parameters ... 
        p_delta_t = self.get_parameter('delta_t')
        p_range = self.get_parameter('range_m')
        p_delay = self.get_parameter('delay_ms')
        p_path = self.get_parameter('path')
        p_poi_id = self.get_parameter('poi_id')

        # ... and print them via ros2 logging.
        self.get_logger().info("Delta_t: %s [sec]." % str(p_delta_t.value))
        self.get_logger().info("Context range: %d [m] around poi id=%s." % (p_range.value, str(p_poi_id.value)))
        self.get_logger().info("Delay: %s [ms]." % str(p_delay.value))
        self.get_logger().info("Path to sumocfg: %s." % p_path.value)

        # Call sumo-gui and open TraCI connection. 
        sumo_cmd = [
            "sumo-gui", 
            "-c", p_path.value, 
            '--step-length', str(p_delta_t.value), 
            '--delay', str(p_delay.value), 
            '--lateral-resolution', str(0.1)]
        traci.start(sumo_cmd)

        # Now, let's subscribe the quantities, we are interested in in a certain context (around a POI, e.g.)
        poi_id = 'label'
        self.get_logger().info("Subscribing vehicle quantities over TraCI.")
        traci.poi.subscribeContext(poi_id, tc.CMD_GET_VEHICLE_VARIABLE, p_range.value, [tc.VAR_POSITION, 
                                                                                        tc.VAR_POSITION3D, 
                                                                                        tc.VAR_ANGLE, 
                                                                                        tc.VAR_SPEED,
                                                                                        tc.VAR_ACCELERATION, 
                                                                                        tc.VAR_WIDTH, 
                                                                                        tc.VAR_LENGTH])
        # Create transform publisher and timing mode.
        self.br = TransformBroadcaster(self)
        self.timer = self.create_timer(p_delta_t.value, self.timer_callback)
        self.i = 0

        # Finalize init() routine
        self.get_logger().info("Vehicle Publisher initialized properly.")


    def timer_callback(self):
        """
        This callback is triggered by a fixed timer to read out our subscribed 
        vehicles' quantities to publish and distribute them over ROS2.
        """
        # 1. Reduce amount of requests by only considering spatially limited context of POI
        poi_id = self.get_parameter('poi_id').value        
        if poi_id in traci.poi.getAllContextSubscriptionResults():
            self.get_logger().debug("Reading subscriptions from POI %s." % poi_id)
            ctx = traci.poi.getContextSubscriptionResults(poi_id)
            if ctx:
                for veh_id, vars in ctx.items():
                    # extract a vehicles quantities
                    self.get_logger().debug(f"Vehicle {veh_id} found at {vars[tc.VAR_POSITION]} with speed {vars[tc.VAR_SPEED]}.")
                    veh_pos2d = vars[tc.VAR_POSITION]
                    veh_pos3d = vars[tc.VAR_POSITION3D]
                    veh_angle = vars[tc.VAR_ANGLE] # in deg
                    veh_speed = vars[tc.VAR_SPEED]
                    # convert pose to transform
                    t = TransformStamped()
                    # Set header
                    t.header.stamp = self.get_clock().now().to_msg()
                    t.header.frame_id = 'map'
                    t.child_frame_id = veh_id + '_frame'
                    # Set translation
                    t.transform.translation.x = veh_pos3d[0]
                    t.transform.translation.y = veh_pos3d[1]
                    t.transform.translation.z = veh_pos3d[2]
                    # Set rotation
                    veh_angle_rad = math.radians(veh_angle)
                    q = quat_from_euler(0, 0, veh_angle_rad)
                    t.transform.rotation.x = q[0]
                    t.transform.rotation.y = q[1]
                    t.transform.rotation.z = q[2]
                    t.transform.rotation.w = q[3]

                    # Send the transformation for this specific vehicle
                    self.br.sendTransform(t)

        # 3. Finally, progress with simulation in time.
        self.i += 1
        traci.simulationStep()


def main(args=None):
    """
    main() routine starts everything in an object-oriented way. 
    All the magic is done within the TrafficLightPublisher node, 
    which is instantiated and started to spin. 
    """
    rclpy.init(args=args)

    vehicle_pub = VehiclePublisher()
    rclpy.spin(vehicle_pub)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    vehicle_pub.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
