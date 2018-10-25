# -*- coding: utf-8 -*-

import re
import os
import click
import os.path
import subprocess
import pexpect


@click.command()
def main():
    """Fix install flash plugin in Ubuntu happen these errors:

     ... Undetermined Error ..."""

    error_tags = ['Undetermined Error', 'Download Failed']

    # Ensure environment language to en_US
    os.environ['LANG'] = 'en_US.UTF-8'
    os.environ['LANGUAGE'] = 'en_US'

    component = 'flashplugin-installer'
    output = subprocess.check_output(
        "aptitude reinstall %s" % component, shell=True).decode('utf-8')

    if any(tag in output for tag in error_tags):
        matched = re.search(r'downloading\s+(\w+:\/\/[^\s]+)', output)
        url = matched.group(1)
        # file_dir = '/var/cache/flashplugin-installer'
        file_dir = os.curdir
        file_path = os.path.join(
            file_dir, os.path.basename(url))

        os.makedirs(file_dir, exist_ok=True)
        os.system('wget -O %s %s' % (file_path, url))
        os.system('dpkg-reconfigure %s' % component)

        # dpkg-reconfigure required terminal size at lease 
        os.environ['LINES'] = "25"
        os.environ['COLUMNS'] = "80"
        child = pexpect.spawn('dpkg-reconfigure flashplugin-installer')
        child.expect('Location to the local file')
        child.send('%s\t\r' % file_path)
        child.wait()


if __name__ == '__main__':
    main()
