# todo(Yadunund): Add copyright.

import sys
from pathlib import Path

import rclpy
from rclpy.node import Node

from bop_toolkit_lib.config import datasets_path
from bop_toolkit_lib.dataset_params import (
    get_camera_params,
    get_model_params,
    get_present_scene_ids,
    get_split_params,
)
from bop_toolkit_lib.inout import load_json, load_scene_gt, load_scene_camera, load_im, load_depth

from ibpc_interfaces.msg import PoseEstimate
from ibpc_interfaces.srv import GetPoseEstimates

class BOPCamera:
    def __init__(self, path, camera_name, img_id):
        self._load_images(path, camera_name, img_id)

    def _load_images(self, path, camera_name, img_id):
        self.im = load_im(f'{path}/rgb_{camera_name}/{img_id:06d}.png')
        self.depth = load_depth(f'{path}/depth_{camera_name}/{img_id:06d}.png')
        if camera_name != 'photoneo':
            self.aolp = load_im(f'{path}/aolp_{camera_name}/{img_id:06d}.png')
            self.dolp = load_im(f'{path}/dolp_{camera_name}/{img_id:06d}.png')
        else:
            self.aolp = None
            self.dolp = None


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
        scene_gt = load_scene_gt(test_split["scene_gt_tpath"].format(scene_id=scene_id))
        for img_id, obj_gts in scene_gt.items():
            request = GetPoseEstimates.Request()
            cam1 = BOPCamera(scene_dir, 'cam1', img_id)
            cam2 = BOPCamera(scene_dir, 'cam2', img_id)
            cam3 = BOPCamera(scene_dir, 'cam3', img_id)
            photoneo = BOPCamera(scene_dir, 'photoneo', img_id)
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

    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
