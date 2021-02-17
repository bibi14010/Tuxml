# tuxml-kci

A bridge with KernelCI to take in account: any configuration file, any kernel version, any gcc compiler 

## Getting started

```
git clone https://github.com/kernelci/kernelci-core
git clone https://github.com/TuxML/tuxml-kci/
cd tuxml-kci
python3 tuxml_kci.py --kernel_version 5.9 --config defconfig
cat kernel/build/bmeta.json 
```

and you should get something like:
```
{
    "arch": "x86_64",
    "build_environment": "gcc-8",
    "build_log": "build.log",
    "build_platform": [
        "Linux",
        "localhost.localdomain",
        "5.3.7-301.fc31.x86_64",
        "#1 SMP Mon Oct 21 19:18:58 UTC 2019",
        "x86_64",
        "x86_64"
    ],
    "build_threads": 10,
    "build_time": 645.82,
    "compiler": "gcc",
    "compiler_version": "8",
    "compiler_version_full": "gcc (GCC) 9.2.1 20190827 (Red Hat 9.2.1-1)",
    "cross_compile": "",
    "defconfig": "none",
    "defconfig_full": "none",
    "status": "PASS",
    "vmlinux_bss_size": 1007616,
    "vmlinux_data_size": 1601984,
    "vmlinux_file_size": 59455512,
    "vmlinux_text_size": 14684375
}
```

## Usages

The solution can work with `defconfig` `randconfig` and `tinyconfig` (note: we force x86_64 architecture right now). 
It's also possible to use an existing `.config` eg:
`wget https://tuxmlweb.istic.univ-rennes1.fr/data/configuration/193488/config; mv config TuxML-193488.config; python3 tuxml_kci.py --kernel_version 5.8 --config TuxML-193488.config` 

```
cat kernel/build/bmeta.json 
{
    "arch": "x86_64",
    "build_environment": "gcc-8",
    "build_log": "build.log",
    "build_platform": [
        "Linux",
        "localhost.localdomain",
        "5.3.7-301.fc31.x86_64",
        "#1 SMP Mon Oct 21 19:18:58 UTC 2019",
        "x86_64",
        "x86_64"
    ],
    "build_threads": 10,
    "build_time": 453.77,
    "compiler": "gcc",
    "compiler_version": "8",
    "compiler_version_full": "gcc (GCC) 9.2.1 20190827 (Red Hat 9.2.1-1)",
    "cross_compile": "",
    "defconfig": "none",
    "defconfig_full": "none",
    "status": "PASS",

    "vmlinux_bss_size": 15622144,
    "vmlinux_data_size": 1398656,
    "vmlinux_file_size": 33559664,
    "vmlinux_text_size": 10488334
}
``` 
indeed, 33.5Mb as in `https://tuxmlweb.istic.univ-rennes1.fr/data/configuration/193488/`
