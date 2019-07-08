# -*- coding: utf-8 -*-

import re
import os
import click
import os.path
import subprocess


@click.command()
def main():
    """Fix virtualbox not working ..."""

    os.system(
        "aptitude reinstall virtualbox virtualbox-dkms virtualbox-ext-pack"
    )
    os.system("modprobe vboxdrv")
    os.system("modprobe vboxnetflt")

    # Fix user groups, so virtualbox could find the usb deivces
    os.system(
        os.path.expanduser(
            os.path.expandvars("adduser ${SUDO_USER} vboxusers")
        )
    )


if __name__ == "__main__":
    main()
