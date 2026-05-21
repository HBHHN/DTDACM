#!/usr/bin/env python3

##################################################
#  Copyright (c) 2026, Marc Rene Zofka,
#  University of Applied Sciences, Heilbronn
#  All rights reserved.
#
#  Multi Sim Publisher provides an example to 
#  controll parallel simulations from the same ros2 
#  node.
#
#  Usage: ros2 run ros2_sumo multi_sim_publisher.py 
#         --ros-args 
#         -p delta_t:=0.1 
#         -p range_m:=500 
#         -p cfg_path:="/home/mzofka/Arbeitsbereich/ros2_ws/src/ros2_sumo/scenarios/Autobahn/autobahn.sumocfg" 
#         -p rou_path:="/home/mzofka/Arbeitsbereich/ros2_ws/src/ros2_sumo/scenarios/Autobahn/autobahn.rou"
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

class MultiSimWrapper(Node):
    """
    """
    def __init__(self):
        # Call ros2 node's init function
        super().__init__('multi_sim_publisher')

        # Declare ros2 parameters for this node.
        self.declare_parameter('delta_t', 0.1)
        self.declare_parameter('range_m', 500.0)
        self.declare_parameter('cfg_path', "/home/user/scenario.sumocfg")
        self.declare_parameter('rou_path', "/home/user/scenario_rou")
        self.declare_parameter('poi_id', "label")

        # Read out ros2 parameters ... 
        p_delta_t = self.get_parameter('delta_t')
        p_range = self.get_parameter('range_m')
        p_cfg_path = self.get_parameter('cfg_path')
        p_rou_path = self.get_parameter('rou_path')
        p_poi_id = self.get_parameter('poi_id')

        # ... and print them via ros2 logging.
        self.get_logger().info("Delta_t: %s [sec]." % str(p_delta_t.value))
        self.get_logger().info("Range_m: %s [m]" % str(p_range.value))
        self.get_logger().info("Path to sumocfg: %s." % p_cfg_path.value)
        self.get_logger().info("Prefix for rou files: %s." % p_rou_path.value)      
        self.get_logger().info("PoI Label: %s." % p_poi_id.value)       

        # Call multiple instances of sumo or sumo-gui 
        # we expect that the route file are given separately and in their prefix form. 
        # Remove --start if you would like sumo-gui be started explicitely (via mouse click on btn)
        sumo_1_cmd = ["sumo-gui", "-c", p_cfg_path.value, "-r", p_rou_path.value + "_1.xml", "--start"]
        sumo_2_cmd = ["sumo-gui", "-c", p_cfg_path.value, "-r", p_rou_path.value + "_2.xml", "--start"]
        sumo_3_cmd = ["sumo-gui", "-c", p_cfg_path.value, "-r", p_rou_path.value + "_3.xml", "--start"]
        
        traci.start(sumo_1_cmd, label="sim1")
        traci.start(sumo_2_cmd, label="sim2")      
        traci.start(sumo_3_cmd, label="sim3")
        
        # Iterate over all connected simulations and subscribe to PoI Context, 
        # reading out vehicle quantities.
        sim_identifier = ["sim1", "sim2", "sim3"]
        for sid in sim_identifier:
            c = traci.getConnection(sid)
            try:
                c.poi.subscribeContext(p_poi_id.value, tc.CMD_GET_VEHICLE_VARIABLE, p_range.value, [tc.VAR_POSITION, tc.VAR_ANGLE, tc.VAR_SPEED, tc.VAR_WIDTH, tc.VAR_LENGTH]) 
            except traci.exceptions.TraCIException as e:  
                self.get_logger().error("Could not subscribe to poi context: %s. TraCI not initialized properly." % e)   
                sys.exit("TraCI not initialized properly.")

        # Create transform publisher and timer.
        #self.br = TransformBroadcaster(self)
        self.timer = self.create_timer(p_delta_t.value, self.timer_callback)
        self.i = 0

        self.get_logger().info(f"MultiSim Node initialized properly: {len(sim_identifier)} simulations")


    def timer_callback(self):
        """
        This callback function is triggered with a fixed frequency.
        """
        self.get_logger().debug("Timer callback")
        
        # Receive all connection obj to connected simulations for comfortable handling
        conn1 = traci.getConnection("sim1")
        conn2 = traci.getConnection("sim2")
        conn3 = traci.getConnection("sim3")
        
        connection = []
        connection.append(conn1)
        connection.append(conn2)
        connection.append(conn3)


        if self.i == 0:
            ####################################################################
            # Only at first time step, insert dedicated vehicle
            ####################################################################
            vehicle_id = "my_autonomous_vehicle"
            vehicle_type_id = "autonomous_taxi" # Vehicle type must exist
            route_id = "my_autonomous_route"  # Route must exist in your route file
            edges = ["entry", "longEdge", "exit"]
            
            try:
                for c in connection:
                    # Register route witin each connected simulation c
                    c.route.add(route_id, edges)
                    
                    # Create new vehicle type witin each connected simulation c
                    c.vehicletype.copy("DEFAULT_VEHTYPE", vehicle_type_id)
                    c.vehicletype.setVehicleClass(vehicle_type_id, "vip")
                    c.vehicletype.setColor(vehicle_type_id, (255,0,0,255))
                    c.vehicle.add(vehID=vehicle_id, routeID=route_id, typeID=vehicle_type_id, depart=3, departLane="best", departPos="base", departSpeed="31")
                    
                    self.get_logger().info(f"[{c.getLabel()}] Added vehicle {vehicle_id} properly.")
            except traci.exceptions.TraCIException as e:    
                self.get_logger().warn(f"Failed to add vehicle: {e}")
            
            # Global ...
            self.get_logger().info(f"Added vehicle {vehicle_id} properly to all simulations.")
        
        elif self.i > 0:
            ###################################################################
            # At all other steps (i>0), let's read out vehicle information
            ###################################################################
            try:
                poi_id = self.get_parameter('poi_id').value
                # iterate over all connections
                for c in connection:
                    sim_id = c.getLabel()
                    if poi_id in c.poi.getAllContextSubscriptionResults():
                        self.get_logger().info("[%s] Reading subscriptions from POI %s." % (sim_id, poi_id))
                        ctx = c.poi.getContextSubscriptionResults(poi_id)
                        if ctx:
                            for veh_id, vars in ctx.items():
                                # extract a vehicles quantities
                                self.get_logger().info(f"[{c.getLabel()}] Vehicle {veh_id} found at {vars[tc.VAR_POSITION]} with speed {vars[tc.VAR_SPEED]}.")
            except traci.exceptions.TraCIException as e:    
                self.get_logger().warn(f"Failed to read vehicle subscriptions: {e}")

        # 3. Finally, progress with simulation in time with each simulation
        self.i += 1
        for c in connection:
            c.simulationStep()
            self.get_logger().info(f"[{c.getLabel()}] MultiSim targets at t={c.simulation.getTime()}")


def main(args=None):
    """
    main() routine starts everything in an object-oriented way. 
    All the magic is done within the TrafficLightPublisher node, 
    which is instantiated and started to spin. 
    """
    rclpy.init(args=args)

    multi_sim = MultiSimWrapper()
    rclpy.spin(multi_sim)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    multi_sim.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
