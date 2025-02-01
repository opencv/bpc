import argparse
import os
import shlex
import threading

from rocker.core import DockerImageGenerator
from rocker.core import get_rocker_version
from rocker.core import RockerExtensionManager
from rocker.core import OPERATIONS_NON_INTERACTIVE

from io import BytesIO
from urllib.request import urlopen
import urllib.request
from zipfile import ZipFile


def get_bop_template(modelname):
    return f"https://huggingface.co/datasets/bop-benchmark/datasets/resolve/main/{modelname}/{modelname}"


def get_ipd_template(modelname):
    return f"https://huggingface.co/datasets/bop-benchmark/{modelname}/resolve/main/{modelname}"


bop_suffixes = [
    "_base.zip",
    "_models.zip",
    "_test_all.zip",
    "_train_pbr.zip",
]

ipd_suffixes = [s for s in bop_suffixes]
ipd_suffixes.append("_val.zip")
ipd_suffixes.append("_test_all.z01")

available_datasets = {
    "ipd": (get_ipd_template("ipd"), ipd_suffixes),
    "lm": (get_bop_template("lm"), bop_suffixes),
}


def fetch_dataset(dataset, output_path):
    (url_base, suffixes) = available_datasets[dataset]
    for suffix in suffixes:

        url = url_base + suffix
        print(f"Downloading from url: {url}")
        with urlopen(url) as zipurlfile:
            with ZipFile(BytesIO(zipurlfile.read())) as zfile:
                zfile.extractall(output_path)


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

    test_parser.add_argument("estimator_image")
    test_parser.add_argument("dataset")
    test_parser.add_argument("--dataset_directory", action="store", default=".")
    test_parser.add_argument("--debug-inside", action="store_true")
    test_parser.add_argument(
        "--tester-image", default="ghcr.io/yadunund/bpc/estimator-tester:latest"
    )

    fetch_parser = sub_parsers.add_parser("fetch")
    fetch_parser.add_argument("dataset", choices=available_datasets.keys())
    fetch_parser.add_argument("--dataset-path", default=".")

    extension_manager = RockerExtensionManager()
    default_args = {"cuda": True, "network": "host"}
    # extension_manager.extend_cli_parser(test_parser, default_args)

    args = main_parser.parse_args()
    args_dict = vars(args)
    if args.subparser_name == "fetch":
        print(f"Fetching dataset {args_dict['dataset']} to {args_dict['dataset_path']}")
        fetch_dataset(args_dict["dataset"], args_dict["dataset_path"])
        print("Fetch complete")
        return

    # Confirm dataset directory is absolute
    args_dict["dataset_directory"] = os.path.abspath(args_dict["dataset_directory"])

    active_extensions = extension_manager.get_active_extensions(args_dict)
    print("Active extensions %s" % [e.get_name() for e in active_extensions])

    tester_args = {
        "network": "host",
        "extension_blacklist": {},
        "operating_mode": OPERATIONS_NON_INTERACTIVE,
        "env": [
            [f"BOP_PATH:/opt/ros/underlay/install/datasets/{args_dict['dataset']}"],
            [f"DATASET_NAME:{args_dict['dataset']}"],
        ],
        "console_output_file": "ibpc_test_output.log",
        "volume": [
            [f"{args_dict['dataset_directory']}:/opt/ros/underlay/install/datasets"]
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
        "network": "host",
        "extension_blacklist": {},
        "console_output_file": "ibpc_zenoh_output.log",
        "operating_mode": OPERATIONS_NON_INTERACTIVE,
        "volume": [],
    }
    zenoh_extensions = extension_manager.get_active_extensions(tester_args)

    print("Buiding zenoh env")
    dig_zenoh = DockerImageGenerator(
        zenoh_extensions, zenoh_args, "eclipse/zenoh:1.1.1"
    )
    exit_code = dig_zenoh.build(**zenoh_args)
    if exit_code != 0:
        print("Build of zenoh failed exiting")
        return exit_code

    def run_instance(dig_instance, args):
        dig_instance.run(**args)

    tester_thread = threading.Thread(target=run_instance, args=(dig_zenoh, zenoh_args))
    tester_thread.start()

    tester_thread = threading.Thread(
        target=run_instance, args=(dig_tester, tester_args)
    )
    tester_thread.start()

    dig = DockerImageGenerator(
        active_extensions, args_dict, args_dict["estimator_image"]
    )

    exit_code = dig.build(**vars(args))
    if exit_code != 0:
        print("Build failed exiting")
        return exit_code

    if args.debug_inside:
        args_dict["command"] = "bash"

    result = dig.run(**args_dict)
    # TODO clean up threads here
    return result
