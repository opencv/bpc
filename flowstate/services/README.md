## Flowstate Service

The Pose Estimators developed can be run as a service on [Intrinsic Flowstate](https://www.intrinsic.ai/) solutions to build applications with robotic systems.

First, build another Docker image that wraps the pose estimator Docker image generated [previously](../README.md#build-and-test-custom-bpc_pose_estimator-image) with some environment variables to communicate with the Intrinsic Platform.

```bash
# Replace POSE_ESTIMATOR_DOCKER_TAG with tag of the pose estimator image generated previously.
# Replace "bpc_pose_estimator_fs:team_name" with a different tag if needed.
cd ~/bpc_ws/bpc/flowstate
docker buildx build -t bpc_pose_estimator_fs:team_name \
  --file Dockerfile.service \
  --build-arg BASE_IMAGE=<POSE_ESTIMATOR_DOCKER_TAG> \
  .

```

Next, save this Docker image locally. Note, the name of the output file must remain `bpc_pose_estimator.tar`.

```bash
docker save bpc_pose_estimator_fs:example -o bpc_pose_estimator.tar

```

Then build a Flowstate Service bundle.

```bash
cd ~/
git clone https://github.com/intrinsic-ai/sdk.git
cd sdk
bazel run //intrinsic/tools/inbuild -- service bundle \
  --manifest ~/bpc_ws/src/bpc/flowstate/services/bpc_pose_estimator.manifest.textproto \
  --oci_image ~/bpc_ws/src/bpc/flowstate/services/bpc_pose_estimator.tar \
  --output ~/bpc_ws/src/bpc/flowstate/services/bpc_pose_estimator.bundle.tar
```

Finally install the Service in a running solution.

```bash
bazel run //intrinsic/tools/inctl -- service install ~/bpc_ws/src/bpc/flowstate/services/bpc_pose_estimator.bundle.tar \
  --cluster CLUSTER_ID \
  --org ORG \
  --registry REGISTRY \
  --skip_direct_upload
```

To uninstall the Service,

```bash
bazel run //intrinsic/tools/inctl -- service uninstall ai.intrinsic.bpc_pose_estimator \
  --solution SOLUTION_ID \
  --org ORG
```
