# todo(Yadunund): Add copyright.

import cv2
from cv_bridge import CvBridge
import numpy as np
from scipy.spatial.transform import Rotation
import sys
from typing import List, Optional, Union

from geometry_msgs.msg import Pose as PoseMsg
from ibpc_interfaces.msg import Camera as CameraMsg
from ibpc_interfaces.msg import Photoneo as PhotoneoMsg
from ibpc_interfaces.msg import PoseEstimate as PoseEstimateMsg
from ibpc_interfaces.srv import GetPoseEstimates

import rclpy
from rclpy.node import Node


# Helper functions
def ros_pose_to_mat(pose: PoseMsg):
    r = Rotation.from_quat(
        [pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w]
    )
    matrix = r.as_matrix()
    pose_matrix = np.eye(4)
    pose_matrix[:3, :3] = matrix
    pose_matrix[:3, 3] = [pose.position.x, pose.position.y, pose.position.z]
    return pose_matrix


class Camera:
    """
    Represents a camera with its pose, intrinsics, and image data,
    initialized from either a CameraMsg or a PhotoneoMsg ROS message.

    Attributes:
        name (str): The name of the camera (taken from the message's frame_id).
        pose (np.ndarray): The 4x4 camera pose matrix (world-to-camera transformation),
                          converted from the ROS message's pose.
        intrinsics (np.ndarray): The 3x3 camera intrinsics matrix, reshaped from the
                                  message's K matrix.
        rgb (np.ndarray): The RGB image data, converted from the ROS message.
        depth (np.ndarray): The depth image data, converted from the ROS message.
        aolp (np.ndarray, optional): The Angle of Linear Polarization data,
                                     converted from the CameraMsg (None for PhotoneoMsg).
        dolp (np.ndarray, optional): The Degree of Linear Polarization data,
                                     converted from the CameraMsg (None for PhotoneoMsg).
    """

    def __init__(self, msg: Union[CameraMsg, PhotoneoMsg]):
        """
        Initializes a new Camera object from a ROS message.

        Args:
            msg: Either a CameraMsg or a PhotoneoMsg ROS message containing
                 camera information.

        Raises:
           TypeError: If the input `msg` is not of the expected type.
        """
        br = CvBridge()

        if not isinstance(msg, (CameraMsg, PhotoneoMsg)):
            raise TypeError("Input message must be of type CameraMsg or PhotoneoMsg")

        self.name: str = (msg.info.header.frame_id,)
        self.pose: np.ndarray = ros_pose_to_mat(msg.pose)
        self.intrinsics: np.ndarray = np.array(msg.info.k).reshape(3, 3)
        self.rgb = br.imgmsg_to_cv2(msg.rgb)
        self.depth = br.imgmsg_to_cv2(msg.depth)
        if isinstance(msg, CameraMsg):
            self.aolp: Optional[np.ndarray] = br.imgmsg_to_cv2(msg.aolp)
            self.dolp: Optional[np.ndarray] = br.imgmsg_to_cv2(msg.dolp)
        else:  # PhotoneoMsg
            self.aolp: Optional[np.ndarray] = None
            self.dolp: Optional[np.ndarray] = None


class PoseEstimator(Node):

    def __init__(self):
        super().__init__("ibp_pose_estimator")
        self.get_logger().info("Starting ibpc_pose_estimator...")
        # Declare parameters
        self.model_dir = (
            self.declare_parameter("model_dir", "").get_parameter_value().string_value
        )
        if self.model_dir == "":
            raise Exception("ROS parameter model_dir not set.")
        self.get_logger().info(f"Model directory set to {self.model_dir}.")
        srv_name = "/get_pose_estimates"
        self.get_logger().info(f"Pose estimates can be queried over srv {srv_name}.")
        self.srv = self.create_service(GetPoseEstimates, srv_name, self.srv_cb)

    def srv_cb(self, request, response):
        if len(request.object_ids) == 0:
            self.get_logger().warn("Received request with empty object_ids.")
            return response
        if len(request.cameras) < 3:
            self.get_logger().warn("Received request with insufficient cameras.")
            return response
        try:
            cam_1 = Camera(request.cameras[0])
            cam_2 = Camera(request.cameras[1])
            cam_3 = Camera(request.cameras[2])
            photoneo = Camera(request.photoneo)
            response.pose_estimates = self.get_pose_estimates(
                request.object_ids, cam_1, cam_2, cam_3, photoneo
            )
        except:
            self.get_logger().error("Error calling get_pose_estimates.")
        return response

    def get_pose_estimates(
        self,
        object_ids: List[int],
        cam_1: Camera,
        cam_2: Camera,
        cam_3: Camera,
        photoneo: Camera,
    ) -> List[PoseEstimateMsg]:

        pose_estimates = []
        print(f"Received request to estimates poses for object_ids: {object_ids}")
        """
            Your implementation goes here.
            msg = PoseEstimateMsg()
            # your logic here.
            pose_estimates.append(msg)
        """
        return pose_estimates


def main(argv=sys.argv):
    rclpy.init(args=argv)

    pose_estimator = PoseEstimator()

    rclpy.spin(pose_estimator)

    rclpy.shutdown()


if __name__ == "__main__":
    main()
