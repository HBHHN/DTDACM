#!/usr/bin/env python3

##################################################
#  Copyright (c) 2025, Marc Rene Zofka,
#  University of Applied Sciences, Heilbronn
#  All rights reserved.
#
#  Traffic Light Publisher  node.
#
#  Usage: ros2 run ros2_sumo traffic_lights_publisher.py --ros-args [...]
##################################################

__author__ = "Marc Rene Zofka"
__email__ = "marc-rene.zofka@hs-heilbronn.de"

import re
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter

from std_msgs.msg import String

import os
import sys
if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

import traci
import traci.constants as tc


class TrafficLightPublisher(Node):
    """
    The TrafficLightPublisher nodes serves as a publishing and subscribing node. 
    The TrafficLight information is received by the TraCI connection and 
    published over ros2 for subsequent nodes. At the same time, it opens dedicated 
    subscribers for each traffic light to support program switching via incoming 
    ros2 topics. This node therefore needs subscriber callbacks as well as a 
    timed function triggering the tx process at a fixed frame rate. 
    """

    def __init__(self):
        # Call ros2 node's init function
        super().__init__('traffic_light_publisher')
        
        # Declare ros2 parameters
        self.declare_parameter('delta_t', 0.1)
        #self.declare_parameter('path', "/home/user/.sumocfg")
        self.declare_parameter('path', "/home/hannah/Workspace/ros2_ws/src/ros2_sumo-v010/ros2_sumo-main/scenarios/TechCampus/techcampus.sumocfg")

        p_delta_t = self.get_parameter('delta_t')
        p_path = self.get_parameter('path')

        self.get_logger().info("Delta_t: %s [sec]." % str(p_delta_t.value))
        self.get_logger().info("Path to sumocfg: %s." % p_path.value)
        
        # Call sumo-gui and open TraCI connection. 
        sumo_cmd = ["sumo-gui", "-c", p_path.value]
        traci.start(sumo_cmd)
        
        # Subscribes to traffic lights over TraCI, which are defined in the scenario. 
        self.get_logger().info("Subscribing to all available traffic lights over TraCI.")
        tl_sub = []
        self.tlid_list = traci.trafficlight.getIDList()

        for id in self.tlid_list:
            
            # 1. Subscribe to traffic light.
            self.get_logger().debug('> Subscribing to tl: "%s"' % id)
            traci.trafficlight.subscribe(id,[tc.TL_PHASE_DURATION,
                                             tc.TL_CURRENT_PHASE,
                                             tc.TL_RED_YELLOW_GREEN_STATE,
                                             tc.TL_NEXT_SWITCH])
            
            # 2. Read out all available traffic light logics for every traffic light
            # We assume that this is fixed within simulation, so we can request it once at the very beginning
            for tll in traci.trafficlight.getAllProgramLogics(id):
                tll_name = tll.getSubID()
                self.get_logger().warn(f"TL {id} Program Logics {tll_name} available.")

            # 3. Catch invalid traffic light names, because they may cause problems with ros2 topics (do not allow '#')
            if "#" in id:
                self.get_logger().warn("Pre-reject subscriber for tls: %s due to naming." % id)
                continue

            # 3. Instantiate a subscriber for every traffic light controller, except previoulsy rejected ones (due to invalid topic name).
            try:
                topic = 'in_tl_' + str(id)
                tls = self.create_subscription(String, topic, lambda msg: self.tlc_cb(msg, topic), 10)
                tl_sub.append(tls)
                self.get_logger().info("Added subscriber for tls: %s." % topic)
            except rclpy.exceptions.InvalidTopicNameException as e:            
                self.get_logger().warn("Rejected subscriber for tls: %s." % topic)
                self.get_logger().warn("%s." % e)

        # Create one general publisher for all traffic light states as a compound string.
        self.publisher_ = self.create_publisher(String, 'out_tls', 10)
        
        # Create timer for publisher in [sec].
        self.timer = self.create_timer(p_delta_t.value, self.timer_callback)
        self.i = 0

    def tlc_cb(self, data, source):
        """
        Callback function for traffic light trigger.
        This function assumes that the string interface
        satisfies the condition and form: 
        program:phase
        """
        self.get_logger().debug(f"Receiving traffic light instruction: '{data.data}' from '{source}'")

        # decode string message 
        request = data.data.split(":")
        req_program = request[0]
        req_phase   = request[1]
        
        # extract substring
        prefix = 'in_tl_'
        topic = str(source)
        if topic.startswith(prefix):
            id = topic[len(prefix):]
            self.get_logger().info(f"Decoded desired TL '{id}' program '{req_program}' and phase '{req_phase}'.")
            
            curr_program = traci.trafficlight.getProgram(id)
            
            traci.trafficlight.setProgram(id, req_program)
            traci.trafficlight.setPhase(id, req_phase)
            
            self.get_logger().info(f"Change tl {id} program from '{curr_program}' to '{req_program}'")
        else:
            self.get_logger().error('Could not extract tl id "%s" from topic.' % id)
        return

    def timer_callback(self):
        """
        This callback is triggered by a fixed timer to read out our subscribed 
        traffic light status to publish it as a compound string over ros2.
        """
        # 1. Read all the subscribed values from traffic lights
        tl_str = ""
        for id in self.tlid_list:
            #print(traci.trafficlight.getSubscriptionResults(id))
            tl_str = tl_str + 'TL_ID: ' + id + ' '
            tl_str = tl_str + str(traci.trafficlight.getSubscriptionResults(id))

        # 2. Assign results to string message, publish over ros2 and then increment counter.
        msg = String()
        msg.data = tl_str

        self.publisher_.publish(msg)
        self.get_logger().debug('Publishing: "%s"' % msg.data)
        self.i += 1

        # 3. Finally, progress with simulation in time.
        traci.simulationStep()



def main(args=None):
    """
    main() routine starts everything in an object-oriented way. 
    All the magic is done within the TrafficLightPublisher node, 
    which is instantiated and started to spin. 
    """
    rclpy.init(args=args)

    tl_pub = TrafficLightPublisher()
    rclpy.spin(tl_pub)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    tl_pub.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
