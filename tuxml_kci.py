#!usr/bin/env python

import argparse
import subprocess
import tarfile
import tempfile
import urllib.request
import calendar
import time
import os

kernel_versions_path = "/shared_volume/kernel_versions"
base_path = "/tuxml-kci"


def argparser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-c",
        "--config",
        help="Use a config that you already have setup with your  .config or randconfig to run with a random"
             "config.",
        default="tinyconfig",
        nargs='?'
    )

    parser.add_argument(
        "-k",
        "--kernel_version",
        help="The kernel version to use",
        nargs='?'
    )

    parser.add_argument(
        "-b",
        "--build_env",
        help="Specify the version of gcc compiler.",
        default="gcc-86",
        nargs='?'
    )

    parser.add_argument(
        "-a",
        "--arch",
        help="The architecture of the kernel, could be x86_64 or x86_32. Precise only with 32 or 64.",
        default="x86_64",
        nargs
        ="?"
    )

    # marker 1 done (squelette du script avec argparse )
    return parser.parse_args()


def download_kernel(kver):
    filename = kver + ".tar.xz"

    # fetch the kernel version at this address
    url = "https://mirrors.edge.kernel.org/pub/linux/kernel/v%s.x/linux-%s" % (kver.strip('.')[0], filename)

    # Check if folder that will contain tarballs exists. If not then create it
    if not (os.path.exists(kernel_versions_path)):
        os.mkdir(kernel_versions_path)

    # If the tarball isn't available locally, then download it otherwise do nothing
    if not (os.path.exists("{}/{}".format(kernel_versions_path, filename))):
        print(f"{filename} is downloading.")
        urllib.request.urlretrieve(url, "{}/{}".format(kernel_versions_path, filename))
    else:
        print(f"{filename} already downladed.")


def extract_kernel(kver):
    filename = kver + ".tar.xz"
    # create a temporary directory where the tarball will be extracted
    extract_dir = tempfile.mkdtemp()
    print('The created temporary directory is %s' % extract_dir)

    # Check if the kernel to extract is actually available
    if not (os.path.exists("{base_path}/{filename}".format(base_path=base_path, filename=filename))):
        tar = tarfile.open("{kvp}/{filename}".format(kvp=kernel_versions_path, filename=filename), "r:xz")
        print(f"Extracting {filename}.")
        tar.extractall(extract_dir)
        tar.close()
        print(f"{filename} has been extracted into {extract_dir}/linux-{kver}")
    return extract_dir


# Remove sources from the extraction folder
def clean_sources(x_kdir):
    os.rmdir("{kdir}".format(kdir=x_kdir))


# The function that will build the kernel with the .config or a randconfig
# suppose that you have already do the step 0, step1 and step2 of the how to build kernel with kernel_ci
# and import everything you have to import to use those command
def build_kernel(b_env, kver, arch, kdir):
    os.chdir("/kernelci-core")

    # get current timestamp and create directory for the output metadata
    current_date = calendar.timegm(time.gmtime())
    output_folder = "/shared_volume/{b_env}_{arch}/{timestamp}_{kver})".format(b_env=b_env, arch=arch, timestamp=current_date, kver=kver)
    os.mkdir(output_folder)

    command = "python3 kci_build build_kernel --build-env=gcc-8 --arch={arch} --kdir={kdir} --output={of} --verbose".format(
        arch=arch, kdir=kdir, of=output_folder)

    subprocess.run(command, shell=True)

    # command = "python3 kci_build install_kernel --tree-name=%s --tree-url=%s --branch=master --kdir=/shared_volume/kernel_versions/%s" % (kver, git_url, current, krnl)
    # # first version, need to change the tree-url and branch value I guess
    # subprocess.run(command, shell=True)


if __name__ == "__main__":
    # Get line parameters
    args = argparser()
    config = args.config
    kver = args.kernel_version
    b_env = args.build_env
    arch = args.arch

    download_kernel(kver)
    extraction_path = extract_kernel(kver)

    build_kernel(b_env, kver, arch, extraction_path)
    clean_sources(extraction_path)
