# ros2_sumo
The colcon package ros2_sumo provides ROS2 interfaces and scenarios for projects with the
DLR traffic simulation framework Simulation of Urban Mobility (SUMO).

The repository is built up as follows:
```bash
├── config
├── launch
├── package.xml
├── README.md
├── requirements.txt
├── ros2_sumo
├── scenarios
├── setup.cfg
├── setup.py
└── requirements.txt
```

## Prerequisites and installation of SUMO
System running Ubuntu 22.04 and ROS2 Humble Hawksbill

For ROS2 install see:
- https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html
- https://www.youtube.com/watch?v=flT3LIIR5qo

Run the following beforehand
```shell
foo@bar:$ sudo apt upgrade && sudo apt update
```

Install DLR SUMO (Version 1.26.0)
```shell
foo@bar:$ sudo add-apt-repository ppa:sumo/stable
foo@bar:$ sudo apt-get update
foo@bar:$ sudo apt-get install sumo sumo-tools sumo-doc
```

Create a ROS2 workspace (i.e. a directory to store your ROS2 things for this project, where in later stages build, install, and log will be automatically created. You only have to create src by hand.).
Afterwards checkout this repository inside your ros2 workspace source folder via
```shell
foo@bar:$ cd Workspace/ros2_ws/src/
foo@bar:$ git clone git@git.it.hs-heilbronn.de:te/zofka/ros2_sumo.git
```

You might need to install some python dependencies from requirements.txt
```shell
foo@bar:$ pip install -r $(find ~/*/src/ -maxdepth 1 -type d -name ros2_sumo)/requirements.txt
```

and build it inside the workspace and source it as follows
```shell
foo@bar:$ cd Workspace/ros2_ws
foo@bar:$ colcon build --symlink-install
foo@bar:$ source install/setup.bash
```

Do not forget to export the environment variable for SUMO_HOME, such as
```shell
export SUMO_HOME="/usr/share/sumo"
```


## Reading and setting Traffic Lights
Now youre able to run the ROS2 node `traffic_lights_publisher.py` using a dedicated scenario (defined via path variable)

```shell
foo@bar:$ os2 run ros2_sumo traffic_lights_publisher --ros-args -p delta_t:=0.1 
-p autostart:=False -p path:="/home/mzofka/Arbeitsbereich/ros2_ws/src/ros2_sumo/scenarios/TechCampus/techcampus.sumocfg"
```

In order to see information in ROS2 you need to start the simulation in SUMO.
After the previous command sumo-gui should show up. In this GUI press the 
play-button (green arrow top left). Then, the published information about all 
traffic lights can be observed via

```shell
foo@bar:$ ros2 topic echo /out_tls
```

In order to stimulate the node's input (only valid, when using the TechCampus Scenario!), 
one can use the ros2 CLI capabilities by triggering the traffic light control interfaces via
```shell
foo@bar:$ ros2 topic pub /in_tl_24950122 std_msgs/String "data: 'my_techcampus_program_1:1'"
```

The message over topic `in_tl_<traffic_light_id>` is composed of the desired 
traffic light program and its phase such as `<program>:<phase>`.


## Reading Vehicles
In order to start the vehicle publisher example, which converts vehicle poses to transforms into a running rviz2 instance,
just adapt the appropriate paths in the launch file, and then execute
```shell
foo@bar:$ ros2 launch ros2_sumo vehicle_publisher_with_rviz2_launch.py
```

## Connection to Arduino

Connect your Arduino via USB.

Run the ros2 node `arduino_readwrite.py`.

```shell
foo@bar:$ ros2 run ros2_sumo arduino_readwrite.py
```

You should now see an `[INFO]` stream, with something like `[arduino_traffic_node]: Sending to Arduino: GG`

There will also be a new topic `/arduino_output` on which the messages from Arduino to ROS2 (simple serial messages) are printed.

Check this topic via

```shell
foo@bar:$ ros2 topic echo /arduino_output
```

Here you should see the printouts defined in your Arduino code.


## Troubleshooting

- If something does not work, you probably forgot to source install/setup.bash in your current terminal.
- If you get no messages on the topics, check if you started the simulation in SUMO GUI (play-button)
- In case you encounter Arduino Serial-Port difficulties (/dev/ttyACM0 or /dev/ttyUSB0) try to solve them using ChatGPT :D


# License
This repository is only for academic and educational purpose 
within the University of Heilbronn. 
