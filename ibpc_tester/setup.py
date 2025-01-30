from setuptools import find_packages, setup

package_name = "ibpc_tester"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Yadunund Vijay",
    maintainer_email="yadunund@gmail.com",
    description="TODO: Package description",
    license="Apache License 2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "ibpc_tester = ibpc_tester.ibpc_tester:main",
        ],
    },
)
