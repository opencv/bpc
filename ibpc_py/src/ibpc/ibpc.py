import argparse
import hashlib
import os
import pathlib
import shlex
import shutil
import signal
import threading
import subprocess

from rocker.core import DockerImageGenerator
from rocker.core import get_rocker_version
from rocker.core import RockerExtensionManager
from rocker.core import OPERATIONS_DRY_RUN
from rocker.core import OPERATIONS_INTERACTIVE
from rocker.core import OPERATIONS_NON_INTERACTIVE

from io import BytesIO
from urllib.request import urlretrieve
import urllib.request
from zipfile import ZipFile
from contextlib import nullcontext

ESTIMATOR_CONTAINER = "bpc_estimator"
TESTER_CONTAINER = "bpc_tester"
ZENOH_CONTAINER = "bpc_zenoh"
DEFAULT_CONTAINER_NAMES = [ESTIMATOR_CONTAINER, ZENOH_CONTAINER, TESTER_CONTAINER]


def get_bop_template(modelname):
    return f"https://huggingface.co/datasets/bop-benchmark/datasets/resolve/main/{modelname}/"


def get_ipd_template(modelname):
    return f"https://huggingface.co/datasets/bop-benchmark/{modelname}/resolve/main/"


def stop_containers(containers=DEFAULT_CONTAINER_NAMES, quiet=False):
    for container_name in containers:
        cmd = ["docker", "kill", container_name]
        if not quiet:
            print(f"Running cmd {cmd}")
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if r.returncode != 0 and not quiet:
            print(
                f"Failed to stop container {container_name}. "
                f"{r.stdout}"
                f"{r.stderr}"
            )
        elif not quiet:
            print(f"Successfully stopped container {container_name}")


bop_suffixes = [
    "_base.zip",
    "_models.zip",
    "_test_all.zip",
    "_train_pbr.zip",
]

ipd_suffixes = [s for s in bop_suffixes]
ipd_suffixes.append("_val.zip")
ipd_suffixes.append("_test_all.z01")

lm_files = {
    "lm_base.zip": "a1d793837d4de0dbd33f04e8b04ce4403c909248c527b2d7d61ef5eac3ef2c39",
    "lm_models.zip": "cb5b5366ce620d41800c7941c2e770036c7c13c178514fa07e6a89fda5ff0e7f",
    "lm_test_all.zip": "28e65e9530b94a87c35f33cba81e8f37bc4d59f95755573dea6e9ca0492f00fe",
    "lm_train_pbr.zip": "b7814cc0cd8b6f0d9dddff7b3ded2a189eacfd2c19fa10b3e332f022930551a9",
}

ipd_core = {
    "ipd_base.zip": "c4943d90040df0737ac617c30a9b4e451a7fc94d96c03406376ce34e5a9724d1",
    "ipd_models.zip": "e7435057b48c66faf3a10353a7ae0bffd63ec6351a422d2c97d4ca4b7e6b797a",
    "ipd_val.zip": "50df37c370557a3cccc11b2e6d5f37f13783159ed29f4886e09c9703c1cad8de",
}

ipd_files = {
    "ipd_test_all.zip": "e1b042f046d7d07f8c8811f7739fb68a25ad8958d1b58c5cbc925f98096eb6f9",
    "ipd_train_pbr.zip": "766efd4a25fc1a297e7d150e6293c485b8c65a56ac5596270d02d7d8c3ba48c0",
    "ipd_train_pbr.z01": "2c032236173761945747613e688d7a903568973b494e2b4ed480be050d774203",
    "ipd_train_pbr.z02": "113c0ffdbd4e9632bee1af581f8fd669c5f0c451409f7a5b9e7ce5630f3550e3",
    "ipd_train_pbr.z03": "196f7a2b6ce23ee7998d68ab7a7e0fcf47cf4bbacfbe2e07f6e2828a79c7c3c1",
    "ipd_test_all.z01": "25ce71feb7d9811db51772e44ebc981d57d9f10c91776707955ab1e616346cb3",
}
ipd_files.update(ipd_core)

available_datasets = {
    "ipd_all": (get_ipd_template("ipd"), ipd_files),
    "ipd": (get_ipd_template("ipd"), ipd_core),
    # "lm": (get_bop_template("lm"), lm_files), #LM doesn't work for bpc so disabling
}


def sha256_file(filename):
    block_size = 65536
    sha256 = hashlib.sha256()
    with open(filename, "rb") as fh:
        while True:
            data = fh.read(block_size)
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()


def fetch_dataset(dataset, output_path, remove_zip_after_extract):
    (url_base, files) = available_datasets[dataset]
    # Before we do anything make sure the directory exists
    dataset_dir = os.path.join(output_path, dataset)
    os.makedirs(dataset_dir, exist_ok=True)
    fetched_files = []
    for suffix in files.keys():

        # Sorted so that zip comes before z01

        url = url_base + suffix

        outfile = os.path.basename(url)
        if os.path.exists(outfile):
            print(f"File {outfile} already present checking hash")
            computed_hash = sha256_file(outfile)
            expected_hash = files[suffix]
            if computed_hash == expected_hash:
                print(f"File {outfile} detected with expected sha256 skipping download")
                fetched_files.append(outfile)
                continue
            else:
                print(
                    f"File {outfile}'s hash {computed_hash} didn't match the expected hash {expected_hash}, downloading again."
                )

        print(f"Downloading from url: {url}")

        (filename, headers) = urlretrieve(url, outfile)
        fetched_files.append(filename)

    for filename in fetched_files:
        # Append shard if found
        if filename[-1].isdigit() and filename[-2].isdigit() and filename[-3] == "z":
            # Let 7z find the other files zipfile can't handle file sharding "multiple disks"
            # With .zXX where XX is a number
            fetched_files.remove(filename)

            # Logic for combining files
            # orig_filename = filename[:-2] + "ip"
            # combined_filename = "combined_" + orig_filename
            # with open(combined_filename,'wb') as zipfile:
            #    with open(orig_filename,'rb') as fd:
            #        print(f"Appending shard {orig_filename} to {combined_filename}")
            #        shutil.copyfileobj(fd, zipfile)
            #    with open(filename,'rb') as fd:
            #        print(f"Appending shard {filename} to {combined_filename}")
            #        shutil.copyfileobj(fd, zipfile)
            # fetched_files.remove(orig_filename)
            # fetched_files.remove(filename)
            # fetched_files.append(combined_filename)

    for filename in fetched_files:
        print(f"Unzipping {filename}")
        extraction_path = dataset_dir
        # BOP Specialization
        if filename.endswith("base.zip"):
            extraction_path = output_path
        subprocess.check_call(["7z", "x", "-y", filename, f"-o{extraction_path}"])
        # with ZipFile(filename) as zfile:
        #    zfile.extractall(output_path)

    if remove_zip_after_extract:
        for filename in fetched_files:
            pathlib.Path(filename).unlink(missing_ok=True)


def main():

    main_parser = argparse.ArgumentParser(
        description="The entry point for the Bin Picking Challenge",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    main_parser.add_argument(
        "-v", "--version", action="version", version="%(prog)s " + get_rocker_version()
    )

    sub_parsers = main_parser.add_subparsers(title="test", dest="subparser_name")
    test_parser = sub_parsers.add_parser("test")

    test_parser.add_argument(
        "estimator_image",
        help="For example ghcr.io/opencv/bpc/bpc_pose_estimator:example or your own build",
    )
    test_parser.add_argument("dataset", choices=available_datasets.keys())
    test_parser.add_argument("--dataset_directory", action="store", default=".")
    test_parser.add_argument("--result_directory", action="store", default=".")
    test_parser.add_argument("--debug-inside", action="store_true")
    test_parser.add_argument(
        "--no-gpu",
        action="store_true",
        help="Don't try to mount an NVIDIA gpu automatically.",
    )
    test_parser.add_argument(
        "--tester-image", default="ghcr.io/opencv/bpc/bpc_tester:latest"
    )

    fetch_parser = sub_parsers.add_parser("fetch")
    fetch_parser.add_argument("dataset", choices=available_datasets.keys())
    fetch_parser.add_argument("--dataset-path", default=".")
    fetch_parser.add_argument(
        "--remove-zip-after-extract",
        default=False,
        action="store_true",
        help="Remove the zip files after extracting to save disk space.",
    )

    extension_manager = RockerExtensionManager()

    args = main_parser.parse_args()
    args_dict = vars(args)
    if args.subparser_name == "fetch":
        dataset_name = args_dict["dataset"]
        dataset_directory = args_dict["dataset_path"]
        print(f"Fetching dataset {dataset_name} to {dataset_directory}")
        fetch_dataset(
            dataset_name, dataset_directory, args_dict["remove_zip_after_extract"]
        )
        print("Fetch complete")
        return

    tester_args = {
        "name": TESTER_CONTAINER,
        "network": "host",
        "extension_blacklist": {},
        "operating_mode": OPERATIONS_NON_INTERACTIVE,
        "env": [
            [f"BOP_PATH=/opt/ros/underlay/install/datasets/"],
            [f"DATASET_NAME={args_dict['dataset']}"],
        ],
        "console_output_file": "ibpc_test_output.log",
        "volume": [
            [
                f"{args_dict['dataset_directory']}:/opt/ros/underlay/install/datasets",
                f"{args_dict['result_directory']}:/submission",
            ]
        ],
    }
    print("Buiding tester env")
    tester_extensions = extension_manager.get_active_extensions(tester_args)
    dig_tester = DockerImageGenerator(
        tester_extensions, tester_args, args_dict["tester_image"]
    )

    exit_code = dig_tester.build(**tester_args)
    if exit_code != 0:
        print("Build of tester failed exiting")
        return exit_code

    zenoh_args = {
        "name": ZENOH_CONTAINER,
        "network": "host",
        "extension_blacklist": {},
        "console_output_file": "ibpc_zenoh_output.log",
        "mode": OPERATIONS_NON_INTERACTIVE,
        "volume": [],
    }
    zenoh_extensions = extension_manager.get_active_extensions(zenoh_args)

    print("Buiding zenoh env")
    dig_zenoh = DockerImageGenerator(
        zenoh_extensions, zenoh_args, "eclipse/zenoh:1.2.1"
    )
    exit_code = dig_zenoh.build(**zenoh_args)
    if exit_code != 0:
        print("Build of zenoh failed exiting")
        return exit_code

    print("Making sure that containers are not left over from previous runs.    ")
    stop_containers(quiet=True)

    args_dict["name"] = ESTIMATOR_CONTAINER
    args_dict["network"] = "host"
    args_dict["extension_blacklist"] = ({},)
    args_dict["volume"] = [[f"{args_dict['dataset']}/models:/opt/ros/underlay/install/3d_models"], ]
    if not args_dict["no_gpu"]:
        args_dict["cuda"] = True
        args_dict["nvidia"] = True

    # Confirm dataset directory is absolute
    args_dict["dataset_directory"] = os.path.abspath(args_dict["dataset_directory"])

    active_extensions = extension_manager.get_active_extensions(args_dict)
    print("Active extensions %s" % [e.get_name() for e in active_extensions])

    dig = DockerImageGenerator(
        active_extensions, args_dict, args_dict["estimator_image"]
    )

    exit_code = dig.build(**vars(args))
    if exit_code != 0:
        print("Build failed exiting")
        return exit_code

    if args.debug_inside:
        args_dict["command"] = "/bin/bash"
        args_dict["mode"] = OPERATIONS_INTERACTIVE

    def run_instance(dig_instance, args, other_instances):
        result = dig_instance.run(**args)
        name = args["name"]
        print(f"{ name } finished with exit code {result} -- stopping others.")
        stop_containers(other_instances, quiet=True)

    zenoh_thread = threading.Thread(
        target=run_instance,
        args=(dig_zenoh, zenoh_args, [TESTER_CONTAINER, ESTIMATOR_CONTAINER]),
    )
    zenoh_thread.start()

    tester_thread = threading.Thread(
        target=run_instance,
        args=(dig_tester, tester_args, [ZENOH_CONTAINER, ESTIMATOR_CONTAINER]),
    )
    tester_thread.start()

    try:
        result = dig.run(**args_dict)
        print(f"Estimator finished with exit code {result}")
        stop_containers(quiet=True)
        return result

    except KeyboardInterrupt:
        # TODO clean up threads here

        print("Stopping all containers.")
        stop_containers()
        tester_thread.join()
        zenoh_thread.join()

    return -1
