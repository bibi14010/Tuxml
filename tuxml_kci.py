#!usr/bin/env python

import argparse 
import subprocess
import tarfile
import urllib.request
from pygments.lexers import make
import os

#importer la librairie avec pyp3 pygments.lexers 



###########################################################
def parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        help ="Use a config that you already have setup with yourconfig.config or randconfig to run with a random"
        "config.",
        default ="randconfig",
        nargs = '?'
    )

    parser.add_argument(
        "--kernel_version",
        help="The kernel version to use",
        nargs='?'
    )
        
    parser.add_argument(
        "--compiler",
        help="Specify the version of gcc compiler.",
        default ="gcc8",
        nargs = '?'
    )

    parser.add_argument(
        "--compile",
        help="go directly to compile",
        nargs='?',
        default='false'
    )
 # marker 1 done (squelette du script avec argparse )
    return parser.parse_args()


def download_kernel(args):
        url = "https://mirrors.edge.kernel.org/pub/linux/kernel/v4.x/linux-" + args + ".tar.xz" 
        downloaded_filename = args + '.tar.xz'
        urllib.request.urlretrieve(url, downloaded_filename)

        fname = args + '.tar.xz' 

        if fname.endswith("tar.xz"):
            tar = tarfile.open(fname, "r:xz")
            tar.extractall()
            tar.close()
            subprocess.call("mv linux-"+args+ " kernel_version", shell = True)

#The function that will build the kernel with the .config or a randconfig
#suppos that you  have already do the step 0, step1 and step2 of the how to build kernel with kernel_ci
#and import everything you have to import to use those command
def kernel(config):
    current = os.getcwd()
    print("current path = " + current)
    os.chdir("../kernelci-core")
    print(os.getcwd()+"\n")
    subprocess.run(args="python3 kci_build build_kernel --arch=x86_64 --build-env=gcc-8 --kdir="+current+"/kernel_version/ --verbose", shell=True, check=True)

if __name__ == "__main__":
    args = parser()
    config = args.config
    kv=args.kernel_version
    c=args.compiler
    cm=args.compile
    current = os.getcwd()    
    
    if cm != True:
    
        if kv is not None:
            download_kernel(kv)
        
        os.chdir("kernel_version")
        subprocess.call('mkdir ./build', shell=True)
        os.chdir(current)
        print(" we are in : " + os.getcwd())
        
        #if randconfig, compute a random config and put it into the build directories of the kernel version.
        if config == 'randconfig':
            current = os.getcwd()
            os.chdir("kernel_version")

            subprocess.call('make tinyconfig', shell=True)
            subprocess.call('mv .config ./build', shell=True)
            config = ".config"
            os.chdir(current)
        
        #else copie the .config file to the build directories of the kernel version.
        else : 
            path_config = os.getcwd()
            subprocess.call("mv "+path_config+"/"+config +" ./kernel_version/build", shell=True)

    print("config argument " +config)
    kernel(config)
