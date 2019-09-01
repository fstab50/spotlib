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


def locate_version_module(directory):
    files = list(filter(lambda x: x.endswith('.py'), os.listdir(directory)))
    return [f for f in files if 'version' in f][0]


def package_name(artifact):
    with open(artifact) as f1:
        f2 = f1.readlines()

    for line in f2:
        if line.startswith('PACKAGE'):
            return line.split(':')[1]
    return None


def update_version(projectname, modulename, force_version):
    major, minor = split_version(current_version(modulename))
    pass


if __name__ == '__main__':

    parser = argparse.ArgumentParser(add_help=False)

    try:

        args, unknown = options(parser)

    except Exception as e:
        stdout_message(str(e), 'ERROR')
        sys.exit(exit_codes['E_BADARG']['Code'])

    PACKAGE = package_name(os.path.join(_root(), 'DESCRIPTION.rst'))
    module = locate_version_module(PACKAGE)

    sys.exit(0)

    if update_version(PACKAGE, module, args.force):
        sys.exit(0)
    else:
        sys.exit(1)
