#!usr/bin/env python

import argparse
import json
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import calendar
import time
import os
import shutil
import stat
import platform
import fnmatch

import elftools.elf.constants as elfconst
import elftools.elf.elffile as elffile
import io


# Hard-coded binary kernel image names for each CPU architecture
KERNEL_IMAGE_NAMES = {
    'arm': ['zImage', 'xipImage'],
    'arm64': ['Image'],
    'arc': ['uImage'],
    'i386': ['bzImage'],
    'mips': ['uImage.gz', 'vmlinux.gz.itb'],
    'riscv': ['Image', 'Image.gz'],
    'x86_64': ['bzImage'],
    'x86': ['bzImage'],
}

# Default section names and their build document keys to look in the ELF file.
# These are supposed to always be available.
DEFAULT_ELF_SECTIONS = [
    (".bss", "vmlinux_bss_size"),
    (".text", "vmlinux_text_size")
]

# Write/Alloc & Alloc constant we need to check for in the ELF sections.
ELF_WA_FLAG = elfconst.SH_FLAGS.SHF_WRITE | elfconst.SH_FLAGS.SHF_ALLOC
ELF_A_FLAG = elfconst.SH_FLAGS.SHF_ALLOC


def calculate_data_size(elf_file):
    """Loop through the ELF file sections and compute the .data size.

    It will look for all SHT_PROGBITS type sections that have the
    SHF_ALLOC or SHF_ALLOC+SHF_WRITE flag set and sum their sizes.

    :param elf_file: The open ELF file.
    :return The .data size or 0.
    """
    data_size = 0

    for section in elf_file.iter_sections():
        elf_flags = section["sh_flags"]
        if all([section["sh_type"] == "SHT_PROGBITS",
                any([elf_flags == ELF_WA_FLAG, elf_flags == ELF_A_FLAG])]):
            data_size += section["sh_size"]

    return data_size


def elfread(path):
    """Read a vmlinux file and extract some info from it.

    Update the build document in place.

    Info extracted:
        0. Size of the .text section.
        1. Size of the .data section.
        2. Size of the .bss section.

    :param path: The path to the vmlinux file.
    :type path: str
    :return A dictionary with the extracted values.
    """
    extracted = {}

    if os.path.isfile(path):
        with io.open(path, mode="rb") as vmlinux_strm:
            elf_file = elffile.ELFFile(vmlinux_strm)

            for elf_sect in DEFAULT_ELF_SECTIONS:
                sect = elf_file.get_section_by_name(elf_sect[0])
                if sect:
                    extracted[elf_sect[1]] = sect["sh_size"]

            data_sect = elf_file.get_section_by_name(".data")
            if data_sect:
                extracted["vmlinux_data_size"] = data_sect["sh_size"]
            else:
                extracted["vmlinux_data_size"] = \
                    calculate_data_size(elf_file)

    return extracted

# sys.path.append(os.path.abspath("/kernelci-core"))
# import kernelci.build as kci_build
# import kernelci.config.build as kci_build_config
kernel_versions_path = "/shared_volume/kernel_versions"
base_path = "/tuxml-kci"

# Hard-coded make targets for each CPU architecture
MAKE_TARGETS = {
    'arm': 'zImage',
    'arm64': 'Image',
    'arc': 'uImage',
}

def argparser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-c",
        "--config",
        help="Use a config that you already have setup with your  .config or randconfig to run with a random"
             "config.",
        default="tinyconfig",
        nargs='?',
        required=True
    )

    parser.add_argument(
        "-k",
        "--kernel_version",
        help="The kernel version to use",
        nargs='?',
        required=True
    )

    parser.add_argument(
        "-b",
        "--build_env",
        help="Specify the version of gcc compiler.",
        default="gcc-8",
        nargs='?',
        required=True
    )

    parser.add_argument(
        "-a",
        "--arch",
        help="The architecture of the kernel, could be x86_64 or x86_32. Precise only with 32 or 64.",
        default="x86_64",
        nargs="?",
        required=True
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
    extract_dir = f"{extract_dir}/linux-{kver}"
    return extract_dir


# The function that will build the kernel with the .config or a randconfig
# suppose that you have already do the step 0, step1 and step2 of the how to build kernel with kernel_ci
# and import everything you have to import to use those command
def build_kernel_old(b_env, kver, arch, kdir):
    os.chdir("/kernelci-core")

    # get current timestamp and create directory for the output metadata
    current_date = calendar.timegm(time.gmtime())
    output_folder = "/shared_volume/{b_env}_{arch}/{timestamp}_{kver})".format(b_env=b_env, arch=arch, timestamp=current_date, kver=kver)
    # kci_build.build_kernel(build_env={'gcc', '', '', '8', 'gcc-8'}, kdir=kdir, arch=arch, verbose=True)

    # command = "python3 kci_build install_kernel --tree-name=%s --tree-url=%s --branch=master --kdir=/shared_volume/kernel_versions/%s" % (kver, git_url, current, krnl)
    # # first version, need to change the tree-url and branch value I guess
    # subprocess.run(command, shell=True)

def print_flush(msg):
    print(msg)
    sys.stdout.flush()

def _output_to_file(cmd, log_file, rel_dir=None):
    open(log_file, 'a').write("#\n# {}\n#\n".format(cmd))
    if rel_dir:
        log_file = os.path.relpath(log_file, rel_dir)
    cmd = "/bin/bash -c '(set -o pipefail; {} 2>&1 | tee -a {})'".format(
        cmd, log_file)
    return cmd

def shell_cmd(cmd, ret_code=False):
    if ret_code:
        return False if subprocess.call(cmd, shell=True) else True
    else:
        return subprocess.check_output(cmd, shell=True).decode()

def _run_make(kdir, arch, target=None, jopt=None, silent=True, cc='gcc',
              cross_compile=None, use_ccache=None, output=None, log_file=None,
              opts=None, cross_compile_compat=None):
    args = ['make']

    if opts:
        args += ['='.join([k, v]) for k, v in opts.items()]

    args += ['-C{}'.format(kdir)]

    if jopt:
        args.append('-j{}'.format(jopt))

    if silent:
        args.append('-s')

    args.append('ARCH={}'.format(arch))

    if cross_compile:
        args.append('CROSS_COMPILE={}'.format(cross_compile))

    if cross_compile_compat:
        args.append('CROSS_COMPILE_COMPAT={}'.format(cross_compile_compat))

    if cc.startswith('clang'):
        args.append('LLVM=1')
    else:
        args.append('HOSTCC={}'.format(cc))

    if use_ccache:
        px = cross_compile if cc == 'gcc' and cross_compile else ''
        args.append('CC="ccache {}{}"'.format(px, cc))
        ccache_dir = '-'.join(['.ccache', arch, cc])
        os.environ.setdefault('CCACHE_DIR', ccache_dir)
    elif cc != 'gcc':
        args.append('CC={}'.format(cc))

    if output:
        # due to kselftest Makefile issues, O= cannot be a relative path
        args.append('O={}'.format(os.path.abspath(output)))

    if target:
        args.append(target)

    cmd = ' '.join(args)
    print_flush(cmd)
    if log_file:
        cmd = _output_to_file(cmd, log_file)
    return shell_cmd(cmd, True)

def _make_defconfig(defconfig, kwargs, extras, verbose, log_file):
    kdir, output_path = (kwargs.get(k) for k in ('kdir', 'output'))
    result = True

    defconfig_kwargs = dict(kwargs)
    defconfig_opts = dict(defconfig_kwargs['opts'])
    defconfig_kwargs['opts'] = defconfig_opts
    tmpfile_fd, tmpfile_path = tempfile.mkstemp(prefix='kconfig-')
    tmpfile = os.fdopen(tmpfile_fd, 'w')
    tmpfile_used = False
    defs = defconfig.split('+')
    target = defs.pop(0)
    for d in defs:
        if d.startswith('KCONFIG_'):
            config, value = d.split('=')
            defconfig_opts[config] = value
            extras.append(d)
        elif d.startswith('CONFIG_'):
            tmpfile.write(d + '\n')
            extras.append(d)
            tmpfile_used = True
        else:
            frag_path = os.path.join(kdir, d)
            if os.path.exists(frag_path):
                with open(frag_path) as frag:
                    tmpfile.write("\n# fragment from : {}\n".format(d))
                    tmpfile.writelines(frag)
                    tmpfile_used = True
                extras.append(os.path.basename(os.path.splitext(d)[0]))
            else:
                print_flush("Fragment not found: {}".format(frag_path))
                result = False
    tmpfile.flush()

    if not _run_make(target=target, **defconfig_kwargs):
        result = False

    if result and tmpfile_used:
        kconfig_frag_name = 'frag.config'
        kconfig_frag = os.path.join(output_path, kconfig_frag_name)
        shutil.copy(tmpfile_path, kconfig_frag)
        os.chmod(kconfig_frag,
                 stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        rel_path = os.path.relpath(output_path, kdir)
        cc = kwargs['cc']
        cc_env = (
            "export LLVM=1" if cc.startswith('clang') else
            "export HOSTCC={cc}\nexport CC={cc}".format(cc=cc)
        )
        cmd = """
set -e
cd {kdir}
{cc_env}
export ARCH={arch}
export CROSS_COMPILE={cross}
export CROSS_COMPILE_COMPAT={cross_compat}
scripts/kconfig/merge_config.sh -O {output} '{base}' '{frag}' {redir}
""".format(kdir=kdir, arch=kwargs['arch'], cc_env=cc_env,
           cross=kwargs['cross_compile'], output=rel_path,
           cross_compat=kwargs['cross_compile_compat'],
           base=os.path.join(rel_path, '.config'),
           frag=os.path.join(rel_path, kconfig_frag_name),
           redir='> /dev/null' if not verbose else '')
        print_flush(cmd.strip())
        if log_file:
            cmd = _output_to_file(cmd, log_file, kdir)
        result = shell_cmd(cmd, True)

    tmpfile.close()
    os.unlink(tmpfile_path)

    return result

def _kernel_config_enabled(dot_config, name):
    return shell_cmd('grep -cq CONFIG_{}=y {}'.format(name, dot_config), True)

def build_kernel(b_env, kdir, arch, defconfig=None, jopt=None,
                 verbose=True, output_path=None, mod_path=None):
    """Build a linux kernel

    *build_env* is a BuildEnvironment object
    *kdir* is the path to the kernel source directory
    *defconfig* is the name of the kernel defconfig
    *jopt* is the -j option to pass to make for parallel builds
    *verbose* is whether to print all the output of the make commands
    *output_path* is the path to the directory where the binaries are made
    *mod_path* is the path to where the modules are installed

    The returned value is True if the build was successful or False if there
    was any build error.
    """
    cc = b_env.split('-')[0]
    cross_compile = ''
    cross_compile_compat = ''
    use_ccache = shell_cmd("which ccache > /dev/null", True)
    if jopt is None:
        jopt = int(shell_cmd("nproc")) + 2
    if not output_path:
        output_path = os.path.join(kdir, 'build')
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    if not mod_path:
        mod_path = os.path.join(output_path, '_modules_')
    build_log = 'build.log'
    log_file = os.path.join(output_path, build_log)
    dot_config = os.path.join(output_path, '.config')
    if os.path.exists(log_file):
        os.unlink(log_file)

    opts = {
        'KBUILD_BUILD_USER': 'KernelCI',
    }

    kwargs = {
        'kdir': kdir,
        'arch': arch,
        'cc': cc,
        'cross_compile': cross_compile,
        'cross_compile_compat': cross_compile_compat,
        'use_ccache': use_ccache,
        'output': output_path,
        'silent': not verbose,
        'log_file': log_file,
        'opts': opts,
    }

    start_time = time.time()
    defconfig_extras = []
    if defconfig:
        result = _make_defconfig(
            defconfig, kwargs, defconfig_extras, verbose, log_file)
    elif os.path.exists(dot_config):
        print_flush("Re-using {}".format(dot_config))
        result = True
    else:
        print_flush("ERROR: Missing kernel config")
        result = False
    if result:
        target = (
            'xipImage' if _kernel_config_enabled(dot_config, 'XIP_KERNEL')
            else MAKE_TARGETS.get(arch)
        )
        result = _run_make(jopt=jopt, target=target, **kwargs)
    mods = _kernel_config_enabled(dot_config, 'MODULES')


    if result and mods:
        result = _run_make(jopt=jopt, target='modules', **kwargs)
    if result and _kernel_config_enabled(dot_config, 'OF_FLATTREE'):
        dts_tree = os.path.join(kdir, 'arch/{}/boot/dts'.format(arch))
        if os.path.exists(dts_tree):
            result = _run_make(target='dtbs', **kwargs)
    build_time = time.time() - start_time

    if result and mods:
        if os.path.exists(mod_path):
            shutil.rmtree(mod_path)
        os.makedirs(mod_path)
        opts.update({
            'INSTALL_MOD_PATH': mod_path,
            'INSTALL_MOD_STRIP': '1',
            'STRIP': "{}strip".format(cross_compile),
        })
        result = _run_make(target='modules_install', **kwargs)

    # kselftest
    if result and "kselftest" in defconfig_extras:
        kselftest_install_path = os.path.join(output_path, '_kselftest_')
        if os.path.exists(kselftest_install_path):
            shutil.rmtree(kselftest_install_path)
        opts.update({
            'INSTALL_PATH': kselftest_install_path,
        })
        #
        # Ideally this should just be a 'make kselftest-install', but
        # due to bugs with O= in kselftest Makefile, this has to be
        # 'make -C tools/testing/selftests install'
        #
        kwargs.update({
            'kdir': os.path.join(kdir, 'tools/testing/selftests')
        })
        opts.update({
            'FORMAT': '.xz',
        })
        # 'gen_tar' target does 'make install' and creates tarball
        result = _run_make(target='gen_tar', **kwargs)

    cc_version_cmd = "{}{} --version 2>&1".format(
        cross_compile if cross_compile and cc == 'gcc' else '', cc)
    cc_version_full = shell_cmd(cc_version_cmd).splitlines()[0]

    bmeta = {
        'build_threads': jopt,
        'build_time': round(build_time, 2),
        'status': 'PASS' if result is True else 'FAIL',
        'arch': arch,
        'cross_compile': cross_compile,
        'compiler': cc,
        'compiler_version': b_env.split('-')[1],
        'compiler_version_full': cc_version_full,
        'build_environment': b_env,
        'build_log': build_log,
        'build_platform': platform.uname(),
    }

    if defconfig:
        defconfig_target = defconfig.split('+')[0]
        bmeta.update({
            'defconfig': defconfig_target,
            'defconfig_full': '+'.join([defconfig_target] + defconfig_extras),
        })
    else:
        bmeta.update({
            'defconfig': 'none',
            'defconfig_full': 'none',
        })

    vmlinux_file = os.path.join(output_path, 'vmlinux')
    if os.path.isfile(vmlinux_file):
        vmlinux_meta = elfread(vmlinux_file)
        bmeta.update(vmlinux_meta)
        bmeta['vmlinux_file_size'] = os.stat(vmlinux_file).st_size

    with open(os.path.join(output_path, 'bmeta.json'), 'w') as json_file:
        json.dump(bmeta, json_file, indent=4, sort_keys=True)

    return result

def install_kernel(kdir, output_path=None, install_path=None, mod_path=None):
    """Install the kernel binaries in a directory for a given built revision

    Installing the kernel binaries into a new directory consists of creating a
    "bmeta.json" file with all the meta-data for the kernel build, copying the
    System.map file, the kernel .config, the build log, the frag.config file,
    all the dtbs and a tarball with all the modules.  This is an intermediate
    step between building a kernel and publishing it via the KernelCI backend.

    *kdir* is the path to the kernel source directory
    *tree_name* is the name of the tree from a build configuration
    *git_branch* is the name of the git branch in the tree
    *git_commit* is the git commit SHA
    *describe* is the "git describe" for the commit
    *describe_v* is the verbose "git describe" for the commit
    *output_path" is the path to the directory where the kernel was built
    *install_path* is the path where to install the kernel
    *mod_path* is the path where the modules were installed

    The returned value is True if it was done successfully or False if an error
    occurred.
    """
    if not install_path:
        install_path = os.path.join(kdir, '_install_')
    if not output_path:
        output_path = os.path.join(kdir, 'build')
    if not mod_path:
        mod_path = os.path.join(output_path, '_modules_')

    #
    # if not git_commit:
    #     git_commit = head_commit(kdir)
    # if not describe:
    #     describe = git_describe(tree_name, kdir)
    # if not describe_v:
    #     describe_v = git_describe_verbose(kdir)

    if os.path.exists(install_path):
        shutil.rmtree(install_path)
    os.makedirs(install_path)

    with open(os.path.join(output_path, 'bmeta.json')) as json_file:
        bmeta = json.load(json_file)

    system_map = os.path.join(output_path, 'System.map')
    if os.path.exists(system_map):
        virt_text = shell_cmd('grep " _text" {}'.format(system_map)).split()[0]
        text_offset = int(virt_text, 16) & (1 << 30)-1  # phys: cap at 1G
        shutil.copy(system_map, install_path)
    else:
        text_offset = None

    dot_config = os.path.join(output_path, '.config')
    dot_config_installed = os.path.join(install_path, 'kernel.config')
    shutil.copy(dot_config, dot_config_installed)

    build_log = os.path.join(output_path, 'build.log')
    shutil.copy(build_log, install_path)

    frags = os.path.join(output_path, 'frag.config')
    if os.path.exists(frags):
        shutil.copy(frags, install_path)

    arch = bmeta['arch']
    boot_dir = os.path.join(output_path, 'arch', arch, 'boot')
    kimage_names = KERNEL_IMAGE_NAMES[arch]
    kimages = []
    kimage_file = None
    for root, _, files in os.walk(boot_dir):
        for name in kimage_names:
            if name in files:
                kimages.append(name)
                image_path = os.path.join(root, name)
                shutil.copy(image_path, install_path)
    if kimages:
        for name in kimage_names:
            if name in kimages:
                kimage_file = name
                break
    if not kimage_file:
        print_flush("Warning: no kernel image found")

    dts_dir = os.path.join(boot_dir, 'dts')
    dtbs = os.path.join(install_path, 'dtbs')
    dtb_list = []
    for root, _, files in os.walk(dts_dir):
        for f in fnmatch.filter(files, '*.dtb'):
            dtb_path = os.path.join(root, f)
            dtb_rel = os.path.relpath(dtb_path, dts_dir)
            dtb_list.append(dtb_rel)
            dest_path = os.path.join(dtbs, dtb_rel)
            dest_dir = os.path.dirname(dest_path)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            shutil.copy(dtb_path, dest_path)
    with open(os.path.join(install_path, 'dtbs.json'), 'w') as json_file:
        json.dump({'dtbs': sorted(dtb_list)}, json_file, indent=4)

    modules_tarball = None
    if os.path.exists(mod_path):
        modules_tarball = 'modules.tar.xz'
        modules_tarball_path = os.path.join(install_path, modules_tarball)
        shell_cmd("tar -C{path} -cJf {tarball} .".format(
            path=mod_path, tarball=modules_tarball_path))

    # 'make gen_tar' creates this tarball path
    kselftest_tarball = 'kselftest-packages/kselftest.tar.xz'
    kselftest_tarball_path = os.path.join(output_path, '_kselftest_',
                                          kselftest_tarball)
    if os.path.exists(kselftest_tarball_path):
        kselftest_tarball = os.path.basename(kselftest_tarball_path)
        shutil.copy(kselftest_tarball_path,
                    os.path.join(install_path, kselftest_tarball))
    else:
        kselftest_tarball = kselftest_tarball_path = None

    build_env = bmeta['build_environment']
    defconfig_full = bmeta['defconfig_full']
    # if not publish_path:
    #     publish_path = '/'.join(item.replace('/', '-') for item in [
    #         tree_name, git_branch, describe, arch, defconfig_full, build_env,
    #     ])

    bmeta.update({
        'kconfig_fragments': 'frag.config' if os.path.exists(frags) else '',
        'kernel_image': kimage_file,
        'kernel_config': os.path.basename(dot_config_installed),
        'system_map': 'System.map' if os.path.exists(system_map) else None,
        'text_offset': '0x{:08x}'.format(text_offset) if text_offset else None,
        'dtb_dir': 'dtbs' if os.path.exists(dtbs) else None,
        'modules': modules_tarball,
        'job': '',
        'git_url': '',
        'git_branch': '',
        'git_describe': '', #TODO fix this later
        'git_describe_v': '',
        'git_commit': '',
        'file_server_resource': '',
        'kselftests': kselftest_tarball,
    })

    with open(os.path.join(install_path, 'bmeta.json'), 'w') as json_file:
        json.dump(bmeta, json_file, indent=4, sort_keys=True)

    return True


if __name__ == "__main__":
    # Get line parameters
    args = argparser()
    config = args.config
    kver = args.kernel_version
    b_env = args.build_env
    arch = args.arch

    download_kernel(kver)
    extraction_path = extract_kernel(kver)


    current_date = calendar.timegm(time.gmtime())
    output_folder = "/shared_volume/{b_env}_{arch}/{timestamp}_{kver}".format(b_env=b_env, arch=arch, timestamp=current_date, kver=kver)

    build_kernel(b_env=b_env, arch=arch, kdir=extraction_path, defconfig=config, output_path=output_folder)
    install_kernel(kdir=extraction_path, output_path=output_folder, install_path=output_folder)

    shutil.rmtree(extraction_path)