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
cd bpc
git checkout baseline_solution
```

#### Fetch the dataset

```bash
cd ~/bpc_ws/bpc
bpc fetch ipd
```
This will download the ipd_base.zip, ipd_models.zip, and ipd_val.zip (approximately 6GB combined). The dataset is also available for manual download on [Hugging Face](https://huggingface.co/datasets/bop-benchmark/ipd).

#### Setup the baseline solution <a name="baseline_solution"></a>
Pull the Baseline Solution code

```bash
cd ~/bpc_ws/bpc
wget https://huggingface.co/DrQY/BOP_baseline_model/resolve/main/models.zip
unzip models.zip
rm models.zip
git clone https://github.com/CIRP-Lab/bpc_baseline
```

#### Build custom bpc_pose_estimator image

```bash
cd ~/bpc_ws/bpc
docker buildx build -t bpc_pose_estimator:example \
    --file ./Dockerfile.estimator \
    --build-arg="MODEL_DIR=models" \
    .
```

#### Run evaluation
```bash
bpc test bpc_pose_estimator:example ipd
```
This will validate the baseline solution pose_estimator image against the local copy of validation dataset.

The console output will show the system getting started and then the output of the estimator. It should look like this
```
[INFO] [1740012020.730088360] [bpc_pose_estimator]: Starting bpc_pose_estimator...
[INFO] [1740012020.731203942] [bpc_pose_estimator]: Model directory set to /opt/ros/underlay/install/models.
[INFO] [1740012020.731942445] [bpc_pose_estimator]: Pose estimates can be queried over srv /get_pose_estimates.
None
(2160, 3840, 3)

0: 736x1280 7 object_18s, 128.3ms
Speed: 24.6ms preprocess, 128.3ms inference, 133.0ms postprocess per image at shape (1, 3, 736, 1280)
(2160, 3840, 3)

0: 736x1280 3 object_18s, 9.3ms
Speed: 10.5ms preprocess, 9.3ms inference, 1.2ms postprocess per image at shape (1, 3, 736, 1280)
(2160, 3840, 3)

0: 736x1280 1 object_18, 8.4ms
Speed: 6.2ms preprocess, 8.4ms inference, 1.2ms postprocess per image at shape (1, 3, 736, 1280)

--- Cost Matrix Stats ---
Shape: (7, 3, 1)
Min: 28.0149, Max: 1364.5308, Mean: 623.8398

Random samples from cost_matrix:
  cost_matrix[6,1,0] = 173.7403
  cost_matrix[2,1,0] = 248.1156
  cost_matrix[2,1,0] = 248.1156
  cost_matrix[4,1,0] = 485.7614
  cost_matrix[5,2,0] = 417.8684
[    -3.5334   -0.013345    -0.35796  -0.0013325  -0.0078956]
[    -4.0632    0.034532    -0.13855    0.003017  -0.0088243]
[    -3.8296    0.063605      1.0484  -0.0020436  -0.0054983]
```

If you would like to interact with the estimator and run alternative commands or anything else in the container you can invoke it with `--debug`

The tester console output will be streamed to the file `ibpc_test_output.log` Use this to see it

```bash
tail -f ibpc_test_output.log
```

The output should look like this
```
[INFO] [1740012109.842616985] [ibpc_tester_node]: Sending request for scene_id 0 img_id 5 for objects array('Q', [18])
[INFO] [1740012112.885330028] [ibpc_tester_node]: Got results: [ibpc_interfaces.msg.PoseEstimate(obj_id=18, score=1.0, pose=geometry_msgs.msg.Pose(position=geometry_msgs.msg.Point(x=-416.64837223125244, y=-26.094635255734246, z=1827.382175127359), orientation=geometry_msgs.msg.Quaternion(x=-0.49402383118887866, y=0.8107506610377319, z=0.2913778253987405, w=-0.11714428159429767)))]
[INFO] [1740012114.688732707] [ibpc_tester_node]: Sending request for scene_id 0 img_id 4 for objects array('Q', [18])
[INFO] [1740012115.749648564] [ibpc_tester_node]: Got results: []
[INFO] [1740012117.618597512] [ibpc_tester_node]: Sending request for scene_id 0 img_id 3 for objects array('Q', [18])
[INFO] [1740012118.372530877] [ibpc_tester_node]: Got results: []
[INFO] [1740012120.165323263] [ibpc_tester_node]: Sending request for scene_id 0 img_id 2 for objects array('Q', [18])
[INFO] [1740012120.960678267] [ibpc_tester_node]: Got results: [ibpc_interfaces.msg.PoseEstimate(obj_id=18, score=1.0, pose=geometry_msgs.msg.Pose(position=geometry_msgs.msg.Point(x=57.24788827455574, y=115.56284164988212, z=1743.2343994553567), orientation=geometry_msgs.msg.Quaternion(x=-0.5231791402158902, y=0.6201425354634018, z=-0.4540152155956859, w=0.36820783120350425)))]
[INFO] [1740012122.785210910] [ibpc_tester_node]: Sending request for scene_id 0 img_id 1 for objects array('Q', [18])
[INFO] [1740012123.547388347] [ibpc_tester_node]: Got results: []
[INFO] [1740012125.326573394] [ibpc_tester_node]: Sending request for scene_id 0 img_id 0 for objects array('Q', [18])
[INFO] [1740012126.340159448] [ibpc_tester_node]: Got results: []
[INFO] [1740012128.110107266] [ibpc_tester_node]: Sending request for scene_id 1 img_id 5 for objects array('Q', [14])
[INFO] [1740012129.545785263] [ibpc_tester_node]: Got results: []
[INFO] [1740012131.361073529] [ibpc_tester_node]: Sending request for scene_id 1 img_id 4 for objects array('Q', [14])
[INFO] [1740012132.147259226] [ibpc_tester_node]: Got results: [ibpc_interfaces.msg.PoseEstimate(obj_id=14, score=1.0, pose=geometry_msgs.msg.Pose(position=geometry_msgs.msg.Point(x=-35.97752237106388, y=-43.980911656229765, z=1944.0234546835902), orientation=geometry_msgs.msg.Quaternion(x=0.014174599411342033, y=0.9705649271073079, z=-0.2395150222156359, w=-0.02086521348458312))), ibpc_interfaces.msg.PoseEstimate(obj_id=14, score=1.0, pose=geometry_msgs.msg.Pose(position=geometry_msgs.msg.Point(x=-96.90862385931379, y=143.68589160899882, z=1952.6883644843913), orientation=geometry_msgs.msg.Quaternion(x=-0.06701874171910106, y=0.904418150941101, z=-0.4204850611501449, w=0.02699277414841591)))]
[INFO] [1740012134.004532155] [ibpc_tester_node]: Sending request for scene_id 1 img_id 3 for objects array('Q', [14])
[INFO] [1740012135.022714779] [ibpc_tester_node]: Got results: [ibpc_interfaces.msg.PoseEstimate(obj_id=14, score=1.0, pose=geometry_msgs.msg.Pose(position=geometry_msgs.msg.Point(x=-23.51472483167864, y=171.62909720091636, z=1828.2759864344675), orientation=geometry_msgs.msg.Quaternion(x=0.1360638802890211, y=-0.575497443478442, z=0.7870454894868807, w=-0.1756380098635505))), ibpc_interfaces.msg.PoseEstimate(obj_id=14, score=1.0, pose=geometry_msgs.msg.Pose(position=geometry_msgs.msg.Point(x=-13.948976251096804, y=-21.14926911681635, z=1780.400756890512), orientation=geometry_msgs.msg.Quaternion(x=0.13112676995472627, y=0.8655358196455856, z=-0.46384908621413723, w=-0.1360056628600247)))]
```

The results will come out as `submission.csv` when the tester is complete.

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
rocker --nvidia --cuda --network=host bpc_pose_estimator:example
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
