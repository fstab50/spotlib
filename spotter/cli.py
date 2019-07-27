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
from botocore.exceptions import ClientError
from spotter.lambda_utils import read_env_variable
from libtools import stdout_message
from spotter.statics import local_config
from spotter.help_menu import menu_body
from spotter.colormap import ColorMap
from spotter import about, Colors, logger
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
    try:
        # check if exists; copy
        if not os.path.exists(_config_dir):
            os.makedirs(_config_dir)

    except OSError:
        fx = inspect.stack()[0][3]
        logger.exception('{}: Problem installing user config files. Exit'.format(fx))
        return False
    return True


def endpoint_duration_calc(duration_days=1, start_time=None, end_time=None):
    try:
        if all(x is None for x in [start_time, end_time]):
            end = datetime.datetime.today()
            duration = datetime.timedelta(days=duration_days)
            start = end - duration
            return start, end

        elif all(isinstance(x, datetime.datetime) for x in [start_time, end_time]):
            start = convert_dt(start_time)
            end = convert_dt(end_time)
    except Exception as e:
        logger.exception(f'Unknown exception while calc start & end duration: {e}')
        sys.exit(exit_codes['E_BADARG']['Code'])
    return  start, end


def retreive_spotprice_data(start_dt, end_dt, debug=False):
    """
    Returns:
        spot price data (dict), unique list of instance sizes (list)
s
    """
    try:
        for region in get_regions():
            client = boto3.client('ec2', region_name=region)
            pricelist = client.describe_spot_price_history(StartTime=start, EndTime=end).get(['SpotPriceHistory'])
            instance_sizes = set([x['InstanceType'] for x in pricelist])
    except ClientError as e:
        return [], []
    return pricelist, instance_sizes


def retreive_spotprice_generator(start_dt, end_dt, debug=False):
    """
    Summary:
        Generator returning up to 1000 data items at once

    Returns:
        spot price data (dict), unique list of instance sizes (list

    """
    for region in get_regions():
        client = boto3.client('ec2', region_name=region)
        paginator = client.get_paginator('describe_spot_price_history')
        page_size= read_env_variable('spotprices_per_page', 500)
        page_iterator = paginator.paginate(
                            StartTime=start_dt,
                            EndTime=end_dt,
                            DryRun=debug,
                            PaginationConfig={'PageSize': page_size}
                        )
    for page in page_iterator:
        yield page['Contents']
    pricelist = client.describe_spot_price_history(StartTime=start, EndTime=end).get(['SpotPriceHistory'])
    instance_sizes = set([x['InstanceType'] for x in pricelist])

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

        for data in retreive_spotprice_data(start, end):
            s3upload(data)

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
