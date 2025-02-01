# Perception Challenge For Bin-Picking

This is the python entrypoint for the Bin Picking Challenge

## Usage

Get a dataset
`bpc fetch lm`


Run tests against a dataset
`bpc test <Pose Estimator Image Name> <datasetname> `

`bpc test ibpc:pose_estimator lm`


## Prerequisites


### Install the package:

In a virtualenv
`pip install ibpc`

Temporary before rocker release of https://github.com/osrf/rocker/pull/317/
`pip uninstall rocker && pip install git+http://github.com/osrf/rocker.git@console_to_file`


### Nvidia Docker (optoinal)
Make sure nvidia_docker is installed if you want cuda.

## Release instructions

```
rm -rf dist/*
python3 -m build --sdist .
twine upload dist/*
```
