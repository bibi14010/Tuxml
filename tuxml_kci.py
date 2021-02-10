#!usr/bin/env python

import argparse
import subprocess
import tarfile
import urllib.request

from pygments.lexers import make
import os
from os import path


###########################################################
def parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        help="Use a config that you already have setup with yourconfig.config or randconfig to run with a random"
             "config.",
        default="randconfig",
        nargs='?'
    )

    parser.add_argument(
        "--kernel_version",
        help="The kernel version to use",
        nargs='?'
    )

    parser.add_argument(
        "--compiler",
        help="Specify the version of gcc compiler.",
        default="gcc6",
        nargs='?'
    )
    # marker 1 done (squelette du script avec argparse )
    return parser.parse_args()


def download_kernel(args):
    url = "https://cdn.kernel.org/pub/linux/kernel/v5.x/linux-" + args + ".tar.xz"
    downloaded_filename = args + '.tar.xz'
    if not (path.exists(downloaded_filename)):
        print(f"{downloaded_filename} is downloading.\n")
        urllib.request.urlretrieve(url, downloaded_filename)
    else:
        print(f"{downloaded_filename} already downladed.")

    dir_name = "linux-" + args
    if not (path.exists(dir_name)):
        fname = args + '.tar.xz'
        tar = tarfile.open(fname, "r:xz")
        print(f"Extracting {fname}.")
        tar.extractall()
        tar.close()
        print(f"{fname} has been extracted into {dir_name}")
    else:
        print(f"{dir_name} has been already extracted.")

    # clean folder and sources
    if (path.exists("kernel")):
        subprocess.call("rm -r -f ./kernel", shell=True)
    subprocess.call(f"mv {dir_name} ./kernel", shell=True)
    os.chdir("kernel")
    print("Cleaning the source code . . .")
    subprocess.call("make distclean", shell=True)
    os.chdir("..")

# The function that will build the kernel with the .config or a randconfig
# suppos that you  have already do the step 0, step1 and step2 of the how to build kernel with kernel_ci
# and import everything you have to import to use those command
def kernel(config):
    current = os.getcwd()
    print(f"{current}")
    os.chdir("../kernelci-core")
    print(os.getcwd() + "\n")
    # ./kci_build build_kernel --defconfig=/home/martin/Desktop/tuxml-kci/kernel/build/ --arch=x86_64 --build-env=gcc-8 --kdir=/home/martin/Desktop/tuxml-kci/kernel/ --verbose
    subprocess.run(
        args="python3 kci_build build_kernel --build-env=gcc-8 --arch=x86_64 --kdir=" + current + "/kernel/ --verbose ",
        shell=True, check=True, capture_output=True)


if __name__ == "__main__":
    # Get line parameters
    args = parser()
    config = args.config
    kv = args.kernel_version
    c = args.compiler

    # Get and unzip kernel archive
    if kv is not None:
        download_kernel(kv)
        current = os.getcwd()

    # Si config est precisee creer le .config et le mettre dans build
    if config == 'tinyconfig' or config == 'randconfig' or config == 'defconfig':
        # rentrer dans le dossier kernel
        os.chdir("kernel")
        print("Trying to make" + config + " into " + os.getcwd())
        # creer la config
        subprocess.call('KCONFIG_ALLCONFIG=../x86_64.config make ' + config, shell=True)
        # subprocess.call('make oldconfig ', shell=True)
        # deplacer la config pour le build de kci
        subprocess.call("mkdir build", shell=True)
        subprocess.call('mv .config ./build', shell=True)
        subprocess.call('make mrproper', shell=True)
        # retour dans le reperoir du script
        os.chdir("..")

    # si path de config donne la mettre dans build
    else :
       path_config = os.getcwd()
       subprocess.call("mv "+path_config+"/"+config +" ./kernel/build", shell=True)

    kernel(os.getcwd() + "/kernel/build/")

# marker 5 done(on lance le build du kernel)

# reste a prendre les outputs
