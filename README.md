# Perception Challenge For Bin-Picking

[![build](https://github.com/Yadunund/ibpc/actions/workflows/build.yaml/badge.svg?branch=main)](https://github.com/Yadunund/ibpc/actions/workflows/build.yaml)
[![style](https://github.com/Yadunund/ibpc/actions/workflows/style.yaml/badge.svg?branch=main)](https://github.com/Yadunund/ibpc/actions/workflows/style.yaml)

For more details on the challenge, [click here](https://bpc.opencv.org/).

## Design

TODO

## Requirements
- [Ubuntu 24.04](https://ubuntu.com/blog/tag/ubuntu-24-04-lts)
- [ROS 2 Jazzy Jalisco](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)
- [Optional] [Docker](https://docs.docker.com/)

> Note: Participants can rely on Docker images if they are unable to setup a native Ubuntu 24.04 environemnt with ROS 2 Jazzy Jalisco.

## Setup

```bash
mkdir ~/ws_ibpc/src -p
cd ~/ws_ibpc/src
git clone https://github.com/Yadunund/bop_toolkit.git -b add_ipd_dataset
git clone https://github.com/Yadunund/ibpc.git
```

## Build

### On Ubuntu 24.04
```bash
cd ~/ws_ibpc/
sudo apt update && sudo apt install ros-jazzy-rmw-zenoh-cpp
rosdep update
rosdep install --from-paths src --ignore-src --rosdistro jazzy -y
colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release
```

### With Docker
Build the `ibpc_pose_estimator`.

```bash
cd ~/ws_ibpc/src/ibpc
docker buildx build -t ibpc:pose_estimator \
    --file ./Dockerfile.estimator \
    --build-arg="MODEL_DIR=models" \
    .
```

Build the `ibpc_tester`.

```bash
cd ~/ws_ibpc/src/ibpc
docker buildx build -t ibpc:tester \
    --file ./Dockerfile.tester \
    --build-arg="DATASET_NAME=ipd" \
    .
```
> Note: The BOP_PATH envar should point to a folder that contains models in the BOP format.
See https://bop.felk.cvut.cz/datasets/ for more details.

## Run

### Start the Zenoh router
```bash
docker run --init --rm --net host eclipse/zenoh:1.1.1 --no-multicast-scouting
```

### Run the pose estimator

#### On Ubuntu 24.04
```bash
cd ~/ws_ibpc/
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_zenoh_cpp
ros2 run ibpc_pose_estimator ibpc_pose_estimator --ros-args -p model_dir:=<PATH>
```

#### With Docker
```bash
docker run --network=host ibpc:pose_estimator
```

### Run the tester

> Note: The BOP_PATH envar should point to a folder that contains models in the BOP format.
See https://bop.felk.cvut.cz/datasets/ for more details.

#### On Ubuntu 24.04
```bash
cd ~/ws_ibpc/
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_zenoh_cpp
export BOP_PATH=<PATH_TO_BOP_DATASETS>
ros2 run ibpc_tester ibpc_tester --ros-args -p datset_name:=<DATASET_NAME>
```

#### With Docker
```bash
docker run --network=host -e BOP_PATH=/opt/ros/underlay/install/datasets -e DATASET_NAME=ipd -v$HOME/ws/ibpc/lm:/opt/ros/underlay/install/datasets/lm -it ibpc:tester

```

#### Query the pose estimator directly
```bash
cd ~/ws_ibpc/
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_zenoh_cpp
ros2 service call /get_pose_estimates ibpc_interfaces/srv/GetPoseEstimates '{}'
```
