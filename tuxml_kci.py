#!usr/bin/env python

import argparse 
import subprocess
import tarfile
import urllib.request
from pygments.lexers import make
import os





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
        default ="gcc6",
        nargs = '?'
    )
 # marker 1 done (squelette du script avec argparse )
    return parser.parse_args()


def download_kernel(args):
        url = "https://cdn.kernel.org/pub/linux/kernel/v4.x/linux-" + args + ".tar.xz" 
        downloaded_filename = args + '.tar.xz'
        urllib.request.urlretrieve(url, downloaded_filename)

        fname = args + '.tar.xz' 

        if fname.endswith("tar.xz"):
            tar = tarfile.open(fname, "r:xz")
            tar.extractall()
            tar.close()
            subprocess.call("mv linux-"+args+ " kernel", shell = True)


if __name__ == "__main__":
    args = parser()
    config = args.config
    kv=args.kernel_version
    c=args.compiler
    
    if kv is not None:
        download_kernel(kv)
#marker 2 done (telecharger et decompresser mon archive kernel dans mon path courant)


    if config == 'randconfig':
        current = os.getcwd()
        os.chdir("kernel")
        config = subprocess.call('make randconfig', shell=True)
        os.chdir(current)

#marker 3 done(générer un randconfig si pas de .config passer sinon le .config reste dans config)
    else : 
        path_config = os.getcwd()
        subprocess.call("mv "+path_config+"/"+config +" ./kernel", shell=True)

    #subprocess.call('build_kernel ' + config + ' x86_64 ' + c + ' ' + path + '/linux-' + kv,shell=True)
#marker 5 done(on lance le build du kernel)

#reste a prendre les outputs
