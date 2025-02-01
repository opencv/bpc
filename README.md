# Perception Challenge For Bin-Picking

[![build](https://github.com/Yadunund/ibpc/actions/workflows/build.yaml/badge.svg?branch=main)](https://github.com/Yadunund/ibpc/actions/workflows/build.yaml)
[![style](https://github.com/Yadunund/ibpc/actions/workflows/style.yaml/badge.svg?branch=main)](https://github.com/Yadunund/ibpc/actions/workflows/style.yaml)

For more details on the challenge, [click here](https://bpc.opencv.org/).

![](../media/bpc.gif)

## Overview

This repository contains the ROS interfaces, sample submission code and evaluation service for the Perception Challenge For Bin-Picking.

- **Estimator:**
  The estimator code represents the sample submission. Participants need to implement their solution by editing the placeholder code in the function `get_pose_estimates` in `ibpc_pose_estimator.py` (or its C++ counterpart). The tester will invoke the participant's solution via a ROS 2 service call over the `/get_pose_estimates` endpoint.

- **Tester:**
  The tester code serves as the evaluation service. A copy of this code will be running on the evaluation server and is provided for reference only. It loads the test dataset, prepares image inputs, invokes the estimator service repeatedly, collects the results, and submits for further evaluation.

- **ROS Interface:**
  The API for the challenge is a ROS service, [GetPoseEstimates](ibpc_interfaces/srv/GetPoseEstimates.srv), over `/get_pose_estimates`. Participants implement the service callback on a dedicated ROS node (commonly referred to as the PoseEstimatorNode) which processes the input data (images and metadata) and returns pose estimation results.

In addition, we provide the [ibpc_py tool](https://github.com/Yadunund/bpc/tree/main/ibpc_py) which facilitates downloading the challenge data and performing various related tasks. Please refer to its README for further details.

## Design

### ROS-based Framework

The core architecture of the challenge is based on ROS 2. Participants are required to respond to a ROS 2 Service request with pose estimation results. The key elements of the architecture are:

- **Service API:**
  The ROS service interface (defined in the [GetPoseEstimates](ibpc_interfaces/srv/GetPoseEstimates.srv) file) acts as the API for the challenge.

- **PoseEstimatorNode:**
  Participants are provided with C++ and Python templates for the PoseEstimatorNode. Your task is to implement the callback function (e.g., `get_pose_estimates`) that performs the required computation. Since the API is simply a ROS endpoint, you can use any of the available [ROS 2 client libraries](https://docs.ros.org/en/jazzy/Concepts/Basic/About-Client-Libraries.html#client-libraries) including C++, Python, Rust, Node.js, or C#. Please use [ROS 2 Jazzy Jalisco](https://docs.ros.org/en/jazzy/index.html).

- **TesterNode:**
  A fully implemented TesterNode is provided that:
  - Uses the bop_toolkit_lib to load the test dataset and prepare image inputs.
  - Repeatedly calls the PoseEstimatorNode service over the `/get_pose_estimates` endpoint.
  - Collects and combines results from multiple service calls.
  - Saves the compiled results to disk in CSV format.

### Containerization

To simplify the evaluation process, Dockerfiles are provided to generate container images for both the PoseEstimatorNode and the TesterNode. This ensures that users can run their models without having to configure a dedicated ROS environment manually.

## Submission Instructions

Participants are expected to modify the estimator code to implement their solution. Once completed, your custom estimator should be containerized using Docker and submitted according to the challenge requirements. More detailed submission instructions will be provided soon.

## Requirements

- [Docker](https://docs.docker.com/)
- [rocker](https://github.com/osrf/rocker)

> Note: Participants are expected to submit Docker containers, so all development workflows are designed with this in mind.

## Setup


```bash
mkdir -p ~/ws_ibpc/src
cd ~/ws_ibpc/src
git clone https://github.com/Yadunund/ibpc.git
```

## Build

### Build the ibpc_pose_estimator

```bash
cd ~/ws_ibpc/src/ibpc
docker buildx build -t ibpc:pose_estimator \
    --file ./Dockerfile.estimator \
    --build-arg="MODEL_DIR=models" \
    .
```

### Build the ibpc_tester

```bash
cd ~/ws_ibpc/src/ibpc
docker buildx build -t ibpc:tester \
    --file ./Dockerfile.tester \
    .
```

## Run

### Start the Zenoh router

```bash
docker run --init --rm --net host eclipse/zenoh:1.1.1 --no-multicast-scouting
```

### Run the pose estimator
We use [rocker](https://github.com/osrf/rocker) to add GPU support to Docker containers. To install rocker, run `pip install rocker` on the host machine. 
```bash
rocker --nvidia --cuda run --network=host ibpc:pose_estimator
```

### Run the tester

> Note: Substitute the <PATH_TO_DATASET> with the location of the IPD dataset you've downloaded.

```bash
docker run --network=host -e BOP_PATH=/opt/ros/underlay/install/datasets -e SPLIT_TYPE=val -v<PATH_TO_DATASET>:/opt/ros/underlay/install/datasets -it ibpc:tester
```

## Next Steps

Stay tuned – more detailed submission instructions and guidelines will be provided soon.
