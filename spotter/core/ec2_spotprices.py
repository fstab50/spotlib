"""

EC2 SpotPrice Utils, GPL v3 License

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
from pyaws.session import boto3_session
from botocore.exceptions import ClientError
from spotter.core import DurationEndpoints
from spotter.lambda_utils import get_regions, read_env_variable
from spotter import logger


class EC2SpotPrices():
    """
        Generator class using pagination to return unlimited
        number of spot price history data dict

    Returns:
        spot price data (generator)

    """
    def __init__(self, start_dt=None, end_dt=None, pagesize=None, debug=False):
        """

        """
        self.ept = DurationEndpoints(start_dt, end_dt, debug)
        self.start, self.end = self.ept.calculate_duration_endpoints(
                                    start_time=start_dt, end_time=end_dt
                                )
        self.regions = get_regions()

    def page_iterators(self, region):
        self.client = boto3.client('ec2', region_name=region)
        self.page_size = read_env_variable('prices_per_page', DEFAULT_DATA) or pagesize
        self.pageconfig = {'PageSize': self.page_size}
        self.paginator = self.client.get_paginator('describe_spot_price_history')
        self.page_iterator = paginator.paginate(
                                StartTime=start_dt,
                                EndTime=end_dt,
                                DryRun=debug,
                                PaginationConfig={'PageSize': page_size}
                            )
        return self.page_iterator

    def spotprice_generator(self, debug=False):
        """
        Summary:
            Generator returning up to 1000 data items at once

        Returns:
            spot price data (generator)

        """
        for paginator in self.regional_paginators():
            try:
                for page in paginator:
                    for price_dict in page['SpotPriceHistory']:
                        yield price_dict
            except ClientError as e:
                logger.exception(f'Boto client error while downloading spot history data: {e}')
                continue
            except Exception as e:
                logger.exception(f'Unknown exception while calc start & end duration: {e}')

    def regional_paginators(self, self.regions):
        for region in self.regions:
            return self.page_iterators(region)
