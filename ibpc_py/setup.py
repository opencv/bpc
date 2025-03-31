#!/usr/bin/env python3

import os
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="ibpc",
    version="0.0.7",
    packages=["ibpc"],
    package_dir={"": "src"},
    # package_data={'ibpc': ['templates/*.em']},
    author="Tully Foote",
    author_email="tullyfoote@intrinsic.ai",
    description="An entrypoint for the Industrial Bin Picking Challenge",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://bpc.opencv.org/",
    license="Apache 2.0",
    install_requires=[
        "empy",
        "rocker>=0.2.18",
    ],
    install_package_data=True,
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "bpc = ibpc.ibpc:main",
        ],
    },
)
