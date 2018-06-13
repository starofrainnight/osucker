#!/usr/bin/env python3

import os
import re
import glob
import click
import fnmatch
import os.path
# import rabird.core
from whichcraft import which
from ordered_set import OrderedSet
from rabird.core.configparser import ConfigParser


def is_desktop_file_valid(path):
    if not os.path.exists(path):
        return False

    config = ConfigParser(interpolation=None)
    try:
        with open(path, 'r') as afile:
            config.readfp(afile)
    except FileNotFoundError:
        return False

    cmd = config.get('Desktop Entry', 'Exec', fallback=None)
    if cmd:
        cmd_parites = re.split('\s+', cmd.strip())
        executable = cmd_parites[0]
        if which(executable):
            return True

    return False


def mime_type_join(alist):
    return ';'.join(OrderedSet(alist))


def desktop_file_exists(file_name):
    paths = [
        os.path.expanduser(os.path.expandvars("~/.local/share/applications")),
        '/usr/local/share/applications',
        '/usr/share/applications',
    ]

    # Append data dirs in $XDG_DATA_DIRS environment
    value = os.environ.get('XDG_DATA_DIRS', '')
    if value:
        paths += value.split(':')

    for apath in paths:
        if os.path.exists(os.path.join(apath, file_name)):
            return True

    return False


def safe_write_cfg(cfg, apath):
    old_file_path = apath + '.old'
    new_file_path = apath + '.new'

    with open(new_file_path, 'w') as fp:
        cfg.write(fp, space_around_delimiters=False)

    try:
        os.remove(old_file_path)
    except:
        pass

    try:
        os.rename(apath, old_file_path)
    except:
        pass

    os.rename(new_file_path, apath)


@click.command()
def main():
    """A command to fix all associations problems in ~/.local/share/applications
    which lead duplicated assocations and mass of xxx-1.desktop, xxx-2.desktop,
    etc.
    """

    base_dir = os.path.expanduser(
        os.path.expandvars("~/.local/share/applications"))

    file_names = os.listdir(base_dir)

    # Abbreviation "df" means "Desktop File"

    # Duplicate desktop file patterns with a series file names
    df_duplicates = dict()
    df_rest = []
    df_removes = []

    # The replacements of desktop files which want to be removed.
    df_replaces = dict()

    for afile_name in file_names:
        # If suffix not equal to ".desktop", we won't parse it .
        if not fnmatch.fnmatch(afile_name, "*.desktop"):
            continue

        if not is_desktop_file_valid(os.path.join(base_dir, afile_name)):
            df_removes.append(afile_name)
            continue

        matched = re.match(r"(.*)\-\d+.desktop", afile_name)
        if matched:
            pattern = matched.group(1)
        else:
            pattern = os.path.splitext(afile_name)[0]

        desktop_files = df_duplicates.setdefault(pattern, [])
        desktop_files.append(afile_name)

    # Filter duplicates that only have one item
    df_filtered = []
    for pattern in df_duplicates.keys():
        if len(df_duplicates[pattern]) <= 1:
            df_filtered.append(pattern)

    for pattern in df_filtered:
        del df_duplicates[pattern]

    for pattern, file_names in df_duplicates.items():
        # Merge all mime types into one unified desktop configuration file.
        standard_file_name = pattern + '.desktop'
        standard_file_path = os.path.join(base_dir, standard_file_name)

        if standard_file_name not in file_names:
            standard_file_name = file_names[0]

        file_names.remove(standard_file_name)

        cfg = ConfigParser(interpolation=None)
        with open(standard_file_path, 'r') as fp:
            cfg.readfp(fp)
        mime_types = OrderedSet(cfg.get('Desktop Entry', 'MimeType',
                                        fallback=[]).split(';'))

        # Merge mime types
        for afile_name in file_names:
            other_cfg = ConfigParser(interpolation=None)
            with open(os.path.join(base_dir, afile_name), 'r') as fp:
                other_cfg.readfp(fp)
            mime_types |= OrderedSet(cfg.get('Desktop Entry', 'MimeType',
                                             fallback=[]).split(';'))

            df_replaces[afile_name] = standard_file_name
            df_removes.append(afile_name)

        cfg.set('Desktop Entry', 'MimeType', mime_type_join(mime_types))

        df_rest.append(standard_file_name)

        click.echo("Overwritting %s ..." % standard_file_path)

        safe_write_cfg(cfg, standard_file_path)

    # Remove all unused desktop files
    for apath in df_removes:
        try:
            apath = os.path.join(base_dir, apath)
            click.echo("Removing %s ..." % apath)
            os.remove(apath)
        except:
            pass

    # Remove all outdated desktop file references
    mime_cfg_files = {
        "mimeapps.list": ConfigParser(interpolation=None),
        "mimeinfo.cache": ConfigParser(interpolation=None),
    }
    # Question: What is '~/.config/mimeapps.list' use for ?
    # Seems it's used by system, if we set this mimeapps.list to user root,
    # system can't set the associations again!

    # References:
    # 1. https://standards.freedesktop.org/mime-apps-spec/mime-apps-spec-latest.html
    # 2. https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-1.1.html

    for mime_cfg_file_name, cfg in mime_cfg_files.items():
        with open(os.path.join(base_dir, mime_cfg_file_name), 'r') as fp:
            cfg.readfp(fp)
        for section in cfg.sections():
            for option in cfg.options(section):
                value = cfg.get(section, option, fallback=None)
                if not value:
                    continue

                old_mime_types = value.split(';')
                new_mime_types = []

                # Remove mime type that reference to not existed desktop file or
                # replace them by it's unified desktop file.
                for mime_type in old_mime_types:
                    if desktop_file_exists(mime_type):
                        new_mime_types.append(mime_type)
                    elif mime_type in df_replaces:
                        new_mime_types.append(df_replaces[mime_type])

                value = mime_type_join(OrderedSet(new_mime_types) - df_removes)
                cfg.set(section, option, value)

        mime_cfg_file_path = os.path.join(base_dir, mime_cfg_file_name)
        click.echo("Fixing %s ..." % mime_cfg_file_path)

        safe_write_cfg(cfg, mime_cfg_file_path)


if __name__ == '__main__':
    main()
