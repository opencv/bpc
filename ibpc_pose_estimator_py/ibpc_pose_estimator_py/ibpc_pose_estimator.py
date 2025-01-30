# todo(Yadunund): Add copyright.

from ibpc_interfaces.srv import GetPoseEstimates

import rclpy
from rclpy.node import Node

import sys


class PoseEstimator(Node):

    def __init__(self):
        super().__init__('ibp_pose_estimator')
        self.get_logger().info("Starting ibpc_pose_estimator...")
        # Declare parameters
        self.model_dir = self.declare_parameter("model_dir", "").get_parameter_value().string_value
        if self.model_dir == "":
          raise Exception("ROS parameter model_dir not set.")
        self.get_logger().info(f"Model directory set to {self.model_dir}.")
        srv_name = self.declare_parameter("service_name", "/get_pose_estimates").get_parameter_value().string_value
        if srv_name == "":
          raise Exception("ROS parameter service_name not set.")
        self.get_logger().info(f"Pose estimates can be queried over srv {srv_name}.")
        self.srv = self.create_service(GetPoseEstimates, srv_name, self.srv_cb)

    def srv_cb(self, request, response):

        return response


def main(argv=sys.argv):
    rclpy.init(args=argv)

    pose_estimator = PoseEstimator()

    rclpy.spin(pose_estimator)

    rclpy.shutdown()


if __name__ == '__main__':
    main()