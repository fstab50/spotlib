#!/usr/bin/env python3
"""

xlines, GPL v3 License

Copyright (c) 2018-2019 Blake Huber

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the 'Software'), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""
import os
import sys
import datetime
import json
import inspect
import argparse
from shutil import copy2 as copyfile
from spotter import about, Colors, logger
from libtools import stdout_message
from spotter.statics import local_config
from spotter.help_menu import menu_body
from spotter.core import linecount, locate_fileobjects, remove_illegal, print_footer, print_header
from spotter.exclusions import ExcludedTypes
from spotter.configure import display_exclusions, main_menupage
from spotter.colormap import ColorMap
from spotter.variables import *


cm = ColorMap()

try:
    from xlines.oscodes_unix import exit_codes
    os_type = 'Linux'
    user_home = os.getenv('HOME')
    splitchar = '/'                                   # character for splitting paths (linux)

except Exception:
    from xlines.oscodes_win import exit_codes         # non-specific os-safe codes
    os_type = 'Windows'
    user_home = os.getenv('username')
    splitchar = '\\'                                  # character for splitting paths (windows)


# globals
container = []
module = os.path.basename(__file__)
iloc = os.path.abspath(os.path.dirname(__file__))     # installed location of modules


def modules_location():
    """Filsystem location of Python3 modules"""
    return os.path.split(os.path.abspath(__file__))[0]


def options(parser, help_menu=False):
    """
    Summary:
        parse cli parameter options

    Returns:
        TYPE: argparse object, parser argument set

    """
    parser.add_argument("-e", "--exclusions", dest='exclusions', action='store_true', required=False)
    parser.add_argument("-C", "--configure", dest='configure', action='store_true', required=False)
    parser.add_argument("-d", "--debug", dest='debug', action='store_true', default=False, required=False)
    parser.add_argument("-h", "--help", dest='help', action='store_true', required=False)
    parser.add_argument("-m", "--multiprocess", dest='multiprocess', default=False, action='store_true', required=False)
    parser.add_argument("-s", "--sum", dest='sum', nargs='*', default=os.getcwd(), required=False)
    parser.add_argument("-n", "--no-whitespace", dest='whitespace', action='store_false', default=True, required=False)
    parser.add_argument("-V", "--version", dest='version', action='store_true', required=False)
    return parser.parse_known_args()


def package_version():
    """
    Prints package version and requisite PACKAGE info
    """
    print(about.about_object)
    sys.exit(exit_codes['EX_OK']['Code'])


def precheck(user_exfiles, user_exdirs, debug):
    """
    Runtime Dependency Checks: postinstall artifacts, environment
    """
    def set_environment():
        lang = 'undefined'
        if os.getenv('LANG') is None:
            lang = '{}export LANG=en_US.UTF-8{}'.format(yl, rst)
        elif 'UTF-8' not in os.getenv('LANG'):
            lang = '{}export LANG=$LANG.UTF-8{}'.format(yl, rst)
        return lang

    _os_configdir = os.path.join(modules_location(), 'config')
    _os_ex_fname = os.path.join(_os_configdir, local_config['EXCLUSIONS']['EX_FILENAME'])
    _os_dir_fname = os.path.join(_os_configdir, local_config['EXCLUSIONS']['EX_DIR_FILENAME'])
    _config_dir = local_config['CONFIG']['CONFIG_DIR']
    _language = set_environment()
    _environment_setup = 'fail' if 'UTF-8' in _language else 'success'

    if debug:
        tab = '\t'.expandtabs(16)
        stdout_message(f'_os_configdir: {_os_configdir}: system py modules location', 'DBUG')
        stdout_message(f'_os_ex_fname: {_os_ex_fname}: system exclusions.list path', 'DBUG')
        stdout_message(f'_os_dir_fname: {_os_dir_fname}: system directories.list file path', 'DBUG')
        stdout_message(f'_configdir: {_config_dir}: user home config file location', 'DBUG')
        stdout_message(f'Environment setup status: {_environment_setup.upper()}')

        if _environment_setup.upper() == 'FAIL':
            _env = _environment_setup.upper()
            msg = f'Environment setting is {_env}. Add the following code in your .bashrc file'
            stdout_message('{}:  {}'.format(msg, _language))

    try:
        # check if exists; copy
        if not os.path.exists(_config_dir):
            os.makedirs(_config_dir)

        # cp system config file to user if user config files absent
        if os.path.exists(_os_ex_fname) and os.path.exists(_os_dir_fname):

            if not os.path.exists(user_exfiles):
                copyfile(_os_ex_fname, user_exfiles)

            if not os.path.exists(user_exdirs):
                copyfile(_os_dir_fname, user_exdirs)

    except OSError:
        fx = inspect.stack()[0][3]
        logger.exception('{}: Problem installing user config files. Exit'.format(fx))
        return False
    return True


def endpoint_duration_calc(duration_days=1, start_time=None, end_time=None):
    try:
        if all(x is None for x in [start_time, end_time])
            end = datetime.datetime.today()
            duration = datetime.timedelta(days=duration_days)
            start = end - duration
            return start, end

        start = convert_dt(start_time)
        end = convert_dt(end_time)
    except Exception as e:
        logger.exception(f'Unknown exception while calc start & end duration: {e}')
        sys.exit(exit_codes['E_BADARG']['Code'])
    return  start, end


def init():

    parser = argparse.ArgumentParser(add_help=False)

    try:
        args, unknown = options(parser)
    except Exception as e:
        help_menu()
        stdout_message(str(e), 'ERROR')
        sys.exit(exit_codes['E_BADARG']['Code'])

    # validate configuration files
    if precheck(ex_files, ex_dirs, args.debug):
        _ct_threshold = set_hicount_threshold() or local_config['CONFIG']['COUNT_HI_THRESHOLD']

    if len(sys.argv) == 1 or args.help:
        help_menu()
        sys.exit(exit_codes['EX_OK']['Code'])

    elif args.version:
        package_version()


    elif args.pull:
        start, end = endpoint_duration_calc(args.start, args.end)

    else:
        stdout_message(
            'Dependency check fail %s' % json.dumps(args, indent=4),
            prefix='AUTH',
            severity='WARNING'
            )
        sys.exit(exit_codes['E_DEPENDENCY']['Code'])

    failure = """ : Check of runtime parameters failed for unknown reason.
    Please ensure you have both read and write access to local filesystem. """
    logger.warning(failure + 'Exit. Code: %s' % sys.exit(exit_codes['E_MISC']['Code']))
    print(failure)
