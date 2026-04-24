import rclpy
from rclpy.node import Node

from std_msgs.msg import String
from sensor_msgs.msg import Image

import cv2 as cv
from cv_bridge import CvBridge
bridge = CvBridge()


class ImageConverter(Node):

    def __init__(self):
        super().__init__('image_converter')
        self.subscription = self.create_subscription(
            Image,
            'image_raw',
            self.converter_callback,
            10)
        self.subscription  # prevent unused variable warning
        self.publisher_= self.create_publisher(Image, 'greyscale_image', 10)

    def converter_callback(self, msg):
        self.cv_image = bridge.imgmsg_to_cv2(msg, msg.encoding)
        self.grey_image = cv.cvtColor(self.cv_image, cv.COLOR_BGR2GRAY)
        msg = bridge.cv2_to_imgmsg(self.grey_image)

        self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)

    image_converter = ImageConverter()

    rclpy.spin(image_converter)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    image_converter.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
