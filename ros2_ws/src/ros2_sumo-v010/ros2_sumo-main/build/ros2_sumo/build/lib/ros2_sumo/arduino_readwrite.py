#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import serial
import threading
import re


class ArduinoTrafficNode(Node):
    def __init__(self):
        super().__init__('arduino_traffic_node')

        self.last_sent_states = None
        self.publisher_ = self.create_publisher(String, 'arduino_output', 10)

        try:
            self.serial_conn = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
            self.get_logger().info('Serial connection established.')
        except serial.SerialException as e:
            self.get_logger().error(f"Failed to connect to serial: {e}")
            return

        # Subscribe to traffic light data
        self.subscription = self.create_subscription(
            String,
            'out_tls',
            self.traffic_light_callback,
            10
        )
        self.get_logger().info("Subscribed to /out_tls topic")

        # Start background thread to read from Arduino
        thread = threading.Thread(target=self.read_from_serial)
        thread.daemon = True
        thread.start()

    def traffic_light_callback(self, msg):
        data = msg.data
        tl_states = data.split('TL_ID:')
        for tl in tl_states:
            if '24950122' in tl:  # or check for multiple IDs here
                match = re.search(r"32: '(.*?)'", tl)
                if match:
                    current_tl_states = match.group(1)
                    if current_tl_states != self.last_sent_states:
                        self.last_sent_states = current_tl_states
                        self.get_logger().info(f"New TL states: {current_tl_states}")
                        self.send_command_to_arduino(current_tl_states + '\n')

    def send_command_to_arduino(self, command):
        self.get_logger().info(f"Sending to Arduino: {command.strip()}")
        self.serial_conn.write(command.encode())

    def read_from_serial(self):
        while rclpy.ok():
            try:
                if self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode('utf-8').strip()
                    if line:
                        msg = String()
                        msg.data = line
                        self.publisher_.publish(msg)
                        self.get_logger().info(f'From Arduino: "{line}"')
            except Exception as e:
                self.get_logger().error(f"Error reading from serial: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = ArduinoTrafficNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

