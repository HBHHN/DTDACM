# README

This tutorial handles the builtup of a Autobahn (Highway) scenario [^1].

Run this scenario via

```shell
foo@bar:~/Workspace/ros2_ws/src/ros2_sumo/scenarios/Autobahn$ sumo-gui -c autobahn.sumocfg
```

```shell
ros2 run ros2_sumo multi_sim_publisher.py --ros-args -p delta_t:=0.1 -p cfg_path:="/home/mzofka/Arbeitsbereich/ros2_ws/src/ros2_sumo/scenarios/Autobahn/autobahn.sumocfg" -p rou_path:="/home/mzofka/Arbeitsbereich/ros2_ws/src/ros2_sumo/scenarios/Autobahn/autobahn.rou"
```

### References

[^1] https://sumo.dlr.de/docs/Tutorials/Autobahn.html


## License

This repository is only to be used for academic research and education within the
University of Applied Sciences Heilbronn.
