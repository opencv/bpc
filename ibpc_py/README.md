# Perception Challenge For Bin-Picking

This is the python entrypoint for the Bin Picking Challenge

For example usage see the README at the root of this repository.


## Prerequisites

- [Docker](https://docs.docker.com/)
 * Docker installed with their user in docker group for passwordless invocations.
- 7z -- `apt install 7zip`
- Python3 with virtualenv  -- `apt install python3-virtualenv`


### Install the package:

In a virtualenv:

`pip install ibpc`

Or to develop clone this and run: 

`pip install -e .`


### Nvidia Docker (optoinal)
Make sure nvidia_docker is installed if you want cuda.

## Release instructions

```
rm -rf dist/*
python3 -m build --sdist .
twine upload dist/*
```
