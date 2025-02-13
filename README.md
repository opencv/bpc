# Perception Challenge For Bin-Picking

[![build_packages](https://github.com/opencv/bpc/actions/workflows/build.yaml/badge.svg?branch=main)](https://github.com/opencv/bpc/actions/workflows/build.yaml)
[![style](https://github.com/opencv/bpc/actions/workflows/style.yaml/badge.svg?branch=main)](https://github.com/opencv/bpc/actions/workflows/style.yaml)
[![test validation](https://github.com/opencv/bpc/actions/workflows/test.yaml/badge.svg?branch=main)](https://github.com/opencv/bpc/actions/workflows/test.yaml)

For more details on the challenge, [click here](https://bpc.opencv.org/).

![](../media/bpc.gif)

## Overview

This repository contains the ROS interfaces, sample submission code and evaluation service for the Perception Challenge For Bin-Picking.

- **Estimator:**
  The estimator code represents the sample submission. Participants need to implement their solution by editing the placeholder code in the function `get_pose_estimates` in `ibpc_pose_estimator.py`. The tester will invoke the participant's solution via a ROS 2 service call over the `/get_pose_estimates` endpoint.

- **Tester:**
  The tester code serves as the evaluation service. A copy of this code will be running on the evaluation server and is provided for reference only. It loads the test dataset, prepares image inputs, invokes the estimator service repeatedly, collects the results, and submits for further evaluation.

- **ROS Interface:**
  The API for the challenge is a ROS service, [GetPoseEstimates](ibpc_interfaces/srv/GetPoseEstimates.srv), over `/get_pose_estimates`. Participants implement the service callback on a dedicated ROS node (commonly referred to as the PoseEstimatorNode) which processes the input data (images and metadata) and returns pose estimation results.

In addition, we provide the [ibpc_py tool](https://github.com/opencv/bpc/tree/main/ibpc_py) which facilitates downloading the challenge data and performing various related tasks. Please refer to its README for further details.

## Design

### ROS-based Framework

The core architecture of the challenge is based on ROS 2. Participants are required to respond to a ROS 2 Service request with pose estimation results. The key elements of the architecture are:

- **Service API:**
  The ROS service interface (defined in the [GetPoseEstimates](ibpc_interfaces/srv/GetPoseEstimates.srv) file) acts as the API for the challenge.

- **PoseEstimatorNode:**
  Participants are provided with Python templates for the PoseEstimatorNode. Your task is to implement the callback function (e.g., `get_pose_estimates`) that performs the required computation. Since the API is simply a ROS endpoint, you can use any of the available [ROS 2 client libraries](https://docs.ros.org/en/jazzy/Concepts/Basic/About-Client-Libraries.html#client-libraries) including C++, Python, Rust, Node.js, or C#. Please use [ROS 2 Jazzy Jalisco](https://docs.ros.org/en/jazzy/index.html).

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


## Validation Setup

### Requirements

- [Docker](https://docs.docker.com/)
 * Docker installed with their user in docker group for passwordless invocations.
- 7z -- `apt install 7zip`
- Python3 with virtualenv  -- `apt install python3-virtualenv`

> Note: Participants are expected to submit Docker containers, so all development workflows are designed with this in mind.


This section will guide you through validating your image.

#### Setup a workspace
```
mkdir -p ~/bpc_ws
```

#### Create a virtual environment 

📄 If you're already working in some form of virtualenv you can continue to use that and install `bpc` in that instead of making a new one. 

```
python3 -m venv ~/bpc_ws/bpc_env
```

#### Activate that virtual env

```
source ~/bpc_ws/bpc_env/bin/activate
```

**For any new shell interacting with the `bpc` command you will have to rerun this source command.**

#### Install bpc 
```
pip install ibpc
```



### Fetch the dataset

```
cd ~/bpc_ws
bpc fetch ipd
```

### Run the test

The test will validate your provided image against the test dataset.
When you build a new image you rerun this test.

**At the moment the published tester is not available.
You will have to build it locally see below in Development to build `ibpc:tester` and pass `--tester-image ibpc:tester` as additional arguments.
The default is `ghcr.io/opencv/bpc/estimator-tester:latest` but that's currently unavailable.

```
bpc test <POSE_ESTIMATOR_DOCKER_TAG> ipd
```

For example:

```
bpc test ghcr.io/opencv/bpc/estimator-example:latest ipd
```
**Substitute your own estimator image for ghcr.io/opencv/bpc/estimator-example:latest it's not currently available.**
If you follow the development build below the argument is `ibpc:pose_estimator`.

The console output will show the system getting started and then the output of the estimator. 

If you would like to interact with the estimator and run alternative commands or anything else in the container you can invoke it with `--debug`

The tester console output will be streamed to the file `ibpc_test_output.log` Use this to see it

```
tail -f ibpc_test_output.log
```

The results will come out as `submission.csv` when the tester is complete.


## Pose Estimator Development

Above you've learned how to validate a system. 
It's time to learn how to create your own Pose Estimator.

### Fetch the source repository

```bash
mkdir -p ~/ws_bpc/src
cd ~/ws_bpc/src
git clone https://github.com/opencv/bpc.git
```

### Build the ibpc_pose_estimator

We will use the following example pose estimator for the demo. 

```bash
cd ~/ws_bpc/src/bpc
docker buildx build -t bpc_pose_estimator:example \
    --file ./Dockerfile.estimator \
    --build-arg="MODEL_DIR=models" \
    .
```

If you use this tag the `bpc` invocation will be as follows where you use the image you just built:

`bpc test bpc_pose_estimator:example ipd`


👷 At this point it is up to you to fork and fill in the implementation of the pose estimator. 👷

### Tips

🐌 **If you are iterating a lot of times with the validation and are frustrated by how long the cuda installation is, you can add it to your Dockerfile as below.**
It will make the image significantly larger, but faster to iterate if you put it higher in the dockerfile. We can't include it in the published image because the image gets too big for hosting and pulling easily.

```
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget software-properties-common gnupg2 \
    && rm -rf /var/lib/apt/lists/*

RUN \
  wget -q https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb && \
  dpkg -i cuda-keyring_1.1-1_all.deb && \
  rm cuda-keyring_1.1-1_all.deb && \
  \
  apt-get update && \
  apt-get -y install cuda-toolkit && \
  rm -rf /var/lib/apt/lists/*
```

### Baseline Solution

We provide a simple baseline solution as a reference for implementing the solution in `ibpc_pose_estimator_py`. Please refer to the [baseline_solution](https://github.com/opencv/bpc/tree/baseline_solution) branch and follow the instructions there.


## Further Details

The above is enough to get you going.
However we want to be open about what else were doing.
You can see the source of the tester and build your own version as follows if you'd like. 

### Build the ibpc_tester

If you want to reproduce the tester image run the following command


This is packaged and built via a github action to `ghcr.io/opencv/bpc/estimator-tester:latest` however this is how to reproduce it. 

```bash
cd ~/ws_bpc/src/bpc
docker buildx build -t bpc_tester:latest \
    --file ./Dockerfile.tester \
    .
```

And then when you invoke `bpc test` append the argument `--tester-image bpc_tester:latest` to use your local build.

### If you would like the training data

Use the command:
```
bpc fetch ipd_all
```


### Manually Run components 

It is possible to manually run the components.
`bpc` shows what it is running on the console output.
Or you can run as outlined below. 


### Start the Zenoh router

```bash
docker run --init --rm --net host eclipse/zenoh:1.2.1 --no-multicast-scouting
```

### Run the pose estimator
We use [rocker](https://github.com/osrf/rocker) to add GPU support to Docker containers. To install rocker, run `pip install rocker` on the host machine.
```bash
rocker --nvidia --cuda --network=host ibpc:pose_estimator
```

### Run the tester

> Note: Substitute the <PATH_TO_DATASET> with the directory that contains the [ipd](https://huggingface.co/datasets/bop-benchmark/ipd/tree/main) dataset. Similarly, substitute <PATH_TO_OUTPUT_DIR> with the directory that should contain the results from the pose estimator. By default, the results will be saved as a `submission.csv` file but this filename can be updated by setting the `OUTPUT_FILENAME` environment variable.

```bash
docker run --network=host -e BOP_PATH=/opt/ros/underlay/install/datasets -e SPLIT_TYPE=val -v<PATH_TO_DATASET>:/opt/ros/underlay/install/datasets -v<PATH_TO_OUTPUT_DIR>:/submission -it ibpc:tester
```

