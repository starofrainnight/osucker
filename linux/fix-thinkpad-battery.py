# -*- coding: utf-8 -*-

import re
import os
import click
import os.path
import subprocess


@click.command()
def main():
    """Fix thinkpad battery not charging.

    You must add "tp_smapi" to /etc/modules first, then install tpacpi-bat
    before run this script.
    """

    os.system("aptitude reinstall tp-smapi-dkms acpi-call-dkms ")

    # Set startThreshold and stopThreshold to 60/90
    os.system("tpacpi-bat -s ST 1 60")
    os.system("tpacpi-bat -s SP 1 99")


if __name__ == "__main__":
    main()
