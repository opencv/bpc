# todo(Yadunund): Add copyright.

import cv2
from cv_bridge import CvBridge
import numpy as np
from pathlib import Path
import sys

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy

from bop_toolkit_lib.config import datasets_path
from bop_toolkit_lib.dataset_params import (
    get_camera_params,
    get_model_params,
    get_present_scene_ids,
    get_split_params,
)
from bop_toolkit_lib.inout import load_json, load_scene_gt, load_scene_camera, load_im, load_depth

from geometry_msgs.msg import Pose as PoseMsg
from ibpc_interfaces.msg import Camera as CameraMsg
from ibpc_interfaces.msg import Photoneo as PhotoneoMsg
from ibpc_interfaces.msg import PoseEstimate as PoseEstimateMsg
from ibpc_interfaces.srv import GetPoseEstimates
from sensor_msgs.msg import Image

from scipy.spatial.transform import Rotation

# Helper functions
def pose_mat_to_ros(rot: np.ndarray, trans: np.ndarray):
    r = Rotation.from_matrix(rot)
    q = r.as_quat()
    msg = PoseMsg()
    msg.orientation.x = q[0]
    msg.orientation.y = q[1]
    msg.orientation.z = q[2]
    msg.orientation.w = q[3]
    msg.position.x = float(trans[0])
    msg.position.y = float(trans[1])
    msg.position.z = float(trans[2])
    return msg


class BOPCamera:
    def __init__(self, path, camera_name, img_id):
        self._load_images(path, camera_name, img_id)
        self._load_camera_params(path, camera_name, img_id)

    def _load_images(self, path, camera_name, img_id):
        self.camera_name = camera_name
        self.depth = load_depth(f'{path}/depth_{self.camera_name}/{img_id:06d}.png')
        if self.camera_name != 'photoneo':
            self.rgb = load_im(f'{path}/rgb_{self.camera_name}/{img_id:06d}.png')[:,:,0]
            self.aolp = load_im(f'{path}/aolp_{self.camera_name}/{img_id:06d}.png')
            self.dolp = load_im(f'{path}/dolp_{self.camera_name}/{img_id:06d}.png')
        else:
            self.rgb = load_im(f'{path}/rgb_{self.camera_name}/{img_id:06d}.png')
            self.aolp = None
            self.dolp = None
        self.br = CvBridge()
    def to_camera_msg(self, node, debug_pub) -> CameraMsg:
        msg = CameraMsg()
        msg.info.header.frame_id = self.camera_name
        # msg.info.header.stamp = node.get_clock().now()
        msg.info.k = self.K.reshape(-1)
        msg.pose = pose_mat_to_ros(self.R, self.t)
        msg.rgb = self.br.cv2_to_imgmsg(self.rgb, "8UC1")
        debug_pub.publish(msg.rgb)
        msg.depth = self.br.cv2_to_imgmsg(self.depth, "32FC1")
        msg.aolp = self.br.cv2_to_imgmsg(self.aolp, "8UC1")
        msg.dolp = self.br.cv2_to_imgmsg(self.dolp, "8UC1")
        return msg
    def to_photoneo_msg(self, node, debug_pub) -> PhotoneoMsg:
        msg = PhotoneoMsg()
        msg.info.header.frame_id = self.camera_name
        # msg.info.header.stamp = node.get_clock().now()
        msg.info.k = self.K.reshape(-1)
        msg.pose = pose_mat_to_ros(self.R, self.t)
        msg.rgb = self.br.cv2_to_imgmsg(self.rgb, "8UC1")
        msg.depth = self.br.cv2_to_imgmsg(self.depth, "32FC1")

    def _load_camera_params(self, path, camera_name, img_id):
        self.camera_params = load_scene_camera(f'{path}/scene_camera_{camera_name}.json')[img_id]
        self.K = self.camera_params['cam_K']
        self.R = self.camera_params['cam_R_w2c']
        self.t = self.camera_params['cam_t_w2c']


def main(argv=sys.argv):
    rclpy.init(args=argv)
    args_without_ros = rclpy.utilities.remove_ros_args(argv)
    node = rclpy.create_node("ibpc_tester_node")

    node.get_logger().info("Tester node started...")
    node.get_logger().info(f"Datasets path is set to {datasets_path}.")

    # Declare parameters.
    node.declare_parameter("dataset_name", "ipd")
    dataset_name = node.get_parameter("dataset_name").get_parameter_value().string_value
    node.get_logger().info("Loading from dataset {dataset_name}.")

    # Debug parameters.
    qos_profile = QoSProfile(
        depth=10,  # Queue size (adjust as needed)
        durability=DurabilityPolicy.TRANSIENT_LOCAL,
        reliability=ReliabilityPolicy.RELIABLE  # or RELIABLE, depending on your needs
    )
    debug_pub = node.create_publisher(Image, "/ibpc_tester_debug_images", qos_profile)

    # Load the test split.
    test_split = get_split_params(datasets_path, dataset_name, "test")
    node.get_logger().info(f"Parsed test split: {test_split}")

    # Create the ROS client to query pose estimates.
    client = node.create_client(GetPoseEstimates, "/get_pose_estimates")
    while not client.wait_for_service(timeout_sec=1.0):
        node.get_logger().info(
            "/get_pose_estimates service not available, waiting again..."
        )
    results = {}
    # Get pose estimates for every image in every scene.
    for scene_id in test_split["scene_ids"]:
        scene_dir = Path(test_split["split_path"]) / "{scene_id:06d}".format(
            scene_id=scene_id
        )
        scene_gt = load_scene_gt(test_split["scene_gt_rgb_photoneo_tpath"].format(scene_id=scene_id))
        for img_id, obj_gts in scene_gt.items():
            request = GetPoseEstimates.Request()
            request.cameras.append(BOPCamera(scene_dir, 'cam1', img_id).to_camera_msg(node, debug_pub))
            request.cameras.append(BOPCamera(scene_dir, 'cam2', img_id).to_camera_msg(node, debug_pub))
            request.cameras.append(BOPCamera(scene_dir, 'cam3', img_id).to_camera_msg(node, debug_pub))
            # request.photoneo = BOPCamera(scene_dir, 'photoneo', img_id).to_photoneo_msg(node)
            # todo(Yadunund): Load corresponding rgb, depth and polarized image for this img_id.
            for obj_gt in obj_gts:
                request.object_ids.append(int(obj_gt["obj_id"]))
            node.get_logger().info(
                f"Sending request for scene_id {scene_id} img_id {img_id} for objects {request.object_ids}"
            )
            future = client.call_async(request)
            rclpy.spin_until_future_complete(node, future)
            if future.result() is not None:
                node.get_logger().info(f"Got results: {future.result().pose_estimates}")
            else:
                node.get_logger().error(
                    "Exception while calling service: %r" % future.exception()
                )
        # todo(Yadunund): Remove break after dataset is fixed.
        break

    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
