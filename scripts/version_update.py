#!/usr/bin/env python3

"""
Handles incremental changes to project version id

Use & Restrictions:
    - version format X.Y.Z
    - x, y, z integers
    - can have 0 as either x, y, or z

"""

import os
import sys
import argparse
import subprocess
from libtools import stdout_message

try:
    from libtools.oscodes_unix import exit_codes
    os_type = 'Linux'
    user_home = os.getenv('HOME')

except Exception:
    from libtools.oscodes_win import exit_codes         # non-specific os-safe codes
    os_type = 'Windows'
    user_home = os.getenv('username')


def _root():
    """Returns root directory of git project repository"""
    cmd = 'git rev-parse --show-toplevel 2>/dev/null'
    return subprocess.getoutput(cmd).strip()


def current_version(module_path):
    with open(module_path) as f1:
        f2 = f1.read()
    return f2.split('=')[1].strip()[1:-1]


def locate_version_module(directory):
    files = list(filter(lambda x: x.endswith('.py'), os.listdir(directory)))
    return [f for f in files if 'version' in f][0]


def increment_version(current):
    major = '.'.join(current.split('.')[:2])
    minor = int(current.split('.')[-1][0]) + 1
    return '.'.join([major, str(minor)])


def options(parser, help_menu=True):
    """
    Summary:
        parse cli parameter options

    Returns:
        TYPE: argparse object, parser argument set

    """
    parser.add_argument("-f", "--force", dest='force', nargs='*', default='', required=False)
    parser.add_argument("-d", "--debug", dest='debug', action='store_true', default=False, required=False)
    parser.add_argument("-h", "--help", dest='help', action='store_true', required=False)
    parser.add_argument("-V", "--version", dest='version', action='store_true', required=False)
    return parser.parse_known_args()


def package_name(artifact):
    with open(artifact) as f1:
        f2 = f1.readlines()
    for line in f2:
        if line.startswith('PACKAGE'):
            return line.split(':')[1]
    return None


def update_signature(version, path):
    """Updates version number module with new"""
    try:
        with open(path, 'w') as f1:
            f1.write("__version__ = '{}'".format(version))
            return True
    except OSError:
        stdout_message('Version module unwriteable. Failed to update version')
    return False


def update_version(force_version=None):
    """
    Summary.
        Increments project version by 1 minor increment
        or hard sets to version signature specified

    Args:
        :force_version (Nonetype): Version signature (x.y.z)
            if version number is hardset insetead of increment

    Returns:
        Success | Failure, TYPE: bool
    """
    PACKAGE = package_name(os.path.join(_root(), 'DESCRIPTION.rst'))
    module_path = locate_version_module(PACKAGE)
    version_new = increment_version(current_version(module_path))
    return update_signature(version_new, module_path)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(add_help=False)

    try:

        args, unknown = options(parser)

    except Exception as e:
        stdout_message(str(e), 'ERROR')
        sys.exit(exit_codes['E_BADARG']['Code'])

    if update_version(args.force):
        sys.exit(0)
    sys.exit(1)