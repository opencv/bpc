# Perception Challenge For Bin-Picking

[![build_packages](https://github.com/opencv/bpc/actions/workflows/build.yaml/badge.svg?branch=main)](https://github.com/opencv/bpc/actions/workflows/build.yaml)
[![style](https://github.com/opencv/bpc/actions/workflows/style.yaml/badge.svg?branch=main)](https://github.com/opencv/bpc/actions/workflows/style.yaml)
[![test validation](https://github.com/opencv/bpc/actions/workflows/test.yaml/badge.svg?branch=main)](https://github.com/opencv/bpc/actions/workflows/test.yaml)

Challenge [official website](https://bpc.opencv.org/).

![](../media/bpc.gif)

## Key Steps for Participation
1. [Set up the local environment](#settingup)
2. [Download training and validation/testing data](#download_train_data)
3. Prepare submission:
    1. [Check the baseline solution for input/output examples](#baseline_solution)
    2. [Build your custom image with your solution and test it locally](#build_custom_bpc_pe)
4. [Submit your solution](#submission)

## Overview

This repository contains the sample submission code, ROS interfaces, and evaluation service for the Perception Challenge For Bin-Picking. The reason we openly share the tester code here is to give participants a chance to validate their submissions before submitting.

- **Estimator:**
  The estimator code represents the sample submission. Participants need to implement their solution by editing the placeholder code in the function `get_pose_estimates` in `ibpc_pose_estimator.py`. The tester will invoke the participant's solution via a ROS 2 service call over the `/get_pose_estimates` endpoint.

- **Tester:**
  The tester code serves as the evaluation service. A copy of this code will be running on the evaluation server and is provided for reference only. It loads the test dataset, prepares image inputs, invokes the estimator service repeatedly, collects the results, and submits for further evaluation.

- **ROS Interface:**
  The API for the challenge is a ROS service, [GetPoseEstimates](ibpc_interfaces/srv/GetPoseEstimates.srv), over `/get_pose_estimates`. Participants implement the service callback on a dedicated ROS node (commonly referred to as the PoseEstimatorNode) which processes the input data (images and metadata) and returns pose estimation results.

In addition, we provide the [ibpc_py tool](https://github.com/opencv/bpc/tree/main/ibpc_py) which facilitates downloading the challenge data and performing various related tasks. You can find the installation guide and examples of its usage below. 

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

## Submission Instructions <a name="submission"></a>

Participants are expected to modify the estimator code to implement their solution. Once completed, your custom estimator should be containerized using Docker and submitted according to the challenge requirements. You can find detailed submission instructions [here](https://bpc.opencv.org/web/challenges/challenge-page/1/submission). Please make sure to register a team to get access to the submission instructions. 

## Setting up <a name="settingup"></a>

The following instructions will guide you through the process of validating your submission locally before official submission.

#### Requirements

- [Docker](https://docs.docker.com/) installed with the user in docker group for passwordless invocations. Ensure Docker Buildx is installed (`docker buildx version`). If not, install it with `apt install docker-buildx-plugin` or `apt install docker-buildx` (distribution-dependent). 
- 7z -- `apt install p7zip-full`
- Python3 with virtualenv  -- `apt install python3-virtualenv`
- The `ibpc` and `rocker` CLI tools are tested on Linux-based machines. Due to known Windows issues, we recommend Windows users develop using [WSL](https://learn.microsoft.com/en-us/windows/wsl/about).

> Note: Participants are expected to submit Docker containers, so all development workflows are designed with this in mind.

#### Setup a workspace
```bash
mkdir -p ~/bpc_ws
```

#### Create a virtual environment 

📄 If you're already working in some form of virtualenv you can continue to use that and install `bpc` in that instead of making a new one. 

```bash
python3 -m venv ~/bpc_ws/bpc_env
```

#### Activate that virtual env

```bash
source ~/bpc_ws/bpc_env/bin/activate
```

For any new shell interacting with the `bpc` command you will have to rerun this source command.

#### Install bpc 

Install the bpc command from the ibpc pypi package. (bpc was already taken :-( )

```bash
pip install ibpc
```

#### Fetch the source repository

```bash
cd ~/bpc_ws
git clone https://github.com/opencv/bpc.git
```

#### Fetch the dataset

```bash
cd ~/bpc_ws/bpc
bpc fetch ipd
```
This will download the ipd_base.zip, ipd_models.zip, and ipd_val.zip (approximately 6GB combined). The dataset is also available for manual download on [Hugging Face](https://huggingface.co/datasets/bop-benchmark/ipd).

#### Quickstart with prebuilt images
```bash
bpc test ghcr.io/opencv/bpc/bpc_pose_estimator:example ipd
```
This will download the prebuilt zenoh, tester, and pose_estimator images and run containers based on them. The pose_estimator image contains an empty get_pose_estimates function. After the containers start, you should see the following in your terminal:
```
[INFO] [1740003838.048516355] [bpc_pose_estimator]: Starting bpc_pose_estimator...
[INFO] [1740003838.049547292] [bpc_pose_estimator]: Model directory set to /opt/ros/underlay/install/models.
[INFO] [1740003838.050190130] [bpc_pose_estimator]: Pose estimates can be queried over srv /get_pose_estimates.
```
### Build and test custom bpc_pose_estimator image <a name="build_custom_bpc_pe"></a>

You can then build custom bpc_pose_estimator image with your updated get_pose_estimates function

```bash
cd ~/bpc_ws/bpc
docker buildx build -t <POSE_ESTIMATOR_DOCKER_TAG> \
    --file ./Dockerfile.estimator \
    --build-arg="MODEL_DIR=models" \
    .
```

and run it with the following command
```bash
bpc test <POSE_ESTIMATOR_DOCKER_TAG> ipd
```

For example: 
```bash
cd ~/bpc_ws/bpc
docker buildx build -t bpc_pose_estimator:example \
    --file ./Dockerfile.estimator \
    --build-arg="MODEL_DIR=models" \
    .
bpc test bpc_pose_estimator:example ipd
```
This will validate your pose_estimator image against the local copy of validation dataset.
When you build a new image you rerun this test.

The console output will show the system getting started and then the output of the estimator. 

If you would like to interact with the estimator and run alternative commands or anything else in the container you can invoke it with `--debug`

The tester console output will be streamed to the file `ibpc_test_output.log` Use this to see it

```bash
tail -f ibpc_test_output.log
```

The results will come out as `submission.csv` when the tester is complete.

### Baseline Solution <a name="baseline_solution"></a>

We provide a simple baseline solution as a reference for implementing the solution in `ibpc_pose_estimator_py`. Please refer to the [baseline_solution](https://github.com/opencv/bpc/tree/baseline_solution) branch and follow the instructions there.


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

## Further Details

The above is enough to get you going.
However we want to be open about what else were doing.
You can see the source of the tester and build your own version as follows if you'd like. 

### If you would like the training data and test data <a name="download_train_data"></a>

Use the command:
```bash
bpc fetch ipd_all
```
The dataset is also available for manual download on [Hugging Face](https://huggingface.co/datasets/bop-benchmark/ipd).

### Manually Run components 

It is possible to manually run the components.
`bpc` shows what it is running on the console output.
Or you can run as outlined below. 


#### Start the Zenoh router

```bash
docker run --init --rm --net host eclipse/zenoh:1.2.1 --no-multicast-scouting
```

#### Run the pose estimator
We use [rocker](https://github.com/osrf/rocker) to add GPU support to Docker containers. To install rocker, run `pip install rocker` on the host machine.
```bash
rocker --nvidia --cuda --network=host --volume <PATH_TO_DATASET>/models:/opt/ros/underlay/install/3d_models -- bpc_pose_estimator:example
```

#### Run the tester

> Note: Substitute the <PATH_TO_DATASET> with the directory that contains the [ipd](https://huggingface.co/datasets/bop-benchmark/ipd/tree/main) dataset. Similarly, substitute <PATH_TO_OUTPUT_DIR> with the directory that should contain the results from the pose estimator. By default, the results will be saved as a `submission.csv` file but this filename can be updated by setting the `OUTPUT_FILENAME` environment variable.

```bash
docker run --network=host -e BOP_PATH=/opt/ros/underlay/install/datasets -e SPLIT_TYPE=val -v<PATH_TO_DATASET>:/opt/ros/underlay/install/datasets -v<PATH_TO_OUTPUT_DIR>:/submission -it bpc_tester:latest
```

### Build the bpc_tester image
Generally not required, but to build the tester image, run the following command:
```bash
cd ~/bpc_ws/bpc
docker buildx build -t bpc_tester:latest \
    --file ./Dockerfile.tester \
    .
```
You can then use your tester image with the bpc tool, as shown in the example below:
```bash
bpc test bpc_pose_estimator:example ipd --tester-image bpc_tester:latest
```
