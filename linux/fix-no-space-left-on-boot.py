# -*- coding: utf-8 -*-

import os
import re
import click
import logging
import os.path
import shutil
import subprocess
import shotatlogging
from pkg_resources import parse_version


def get_version_pattern():
    return r"(\d+\.\d+\.\d+\-\d+)"


def get_current_kernel_version():
    version = subprocess.check_output(
        'uname -r', shell=True).decode('utf-8')
    pattern = get_version_pattern()
    matched = re.search(pattern, version)
    version = parse_version(matched.group(1))

    return version


def get_outdated_kernel_packages():
    output = subprocess.check_output(
        'dpkg --get-selections', shell=True).decode('utf-8')
    lines = output.splitlines()
    vpattern = get_version_pattern()
    packages = []
    max_version = None
    for line in lines:
        matched = re.search(r'(linux\-[^\s]*' + vpattern + r'[^\s]*)', line)
        if not matched:
            continue

        version = parse_version(matched.group(2))
        if max_version:
            if version > max_version:
                max_version = version
        else:
            max_version = version
        packages.append((matched.group(1), version))

    outdated = []
    for package, version in packages:
        if version < max_version:
            outdated.append(package)

    return outdated


def clean_modules_dir(keep_version):
    modules_dir = '/lib/modules'
    files = os.listdir(modules_dir)
    vpattern = get_version_pattern()
    junks = []
    for file_name in files:
        apath = os.path.join(modules_dir, file_name)
        if not os.path.isdir(apath):
            continue

        matched = re.search(vpattern, file_name)
        if not matched:
            continue

        version = parse_version(matched.group(1))
        if version < keep_version:
            junks.append(apath)

    for junk in junks:
        print("Removing %s ..." % junk)
        shutil.rmtree(junk, ignore_errors=True)


@click.command()
def main():
    """Fix failed during update-initramfs.

    gzip: stdout: No space left on device
    """

    shotatlogging.setup()

    logger = logging.getLogger()

    kernel_version = get_current_kernel_version()

    print("Current kernel version : %s" % kernel_version)

    packages = get_outdated_kernel_packages()
    for package in packages:
        subprocess.check_call(r"apt purge -y %s" % package, shell=True)

    subprocess.check_call(r'apt autoremove', shell=True)

    # Clean outdated directories in /lib/modules/
    clean_modules_dir(kernel_version)


if __name__ == '__main__':
    main()
