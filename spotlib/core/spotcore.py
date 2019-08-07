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
import boto3
from botocore.exceptions import ClientError
from spotlib.core import DurationEndpoints
from spotlib.core.utc import utc_conversion
from spotlib.lambda_utils import get_regions
from spotlib import logger


class EC2SpotPrices():
    """
        Generator class using pagination to return unlimited
        number of spot price history data dict

    Use:
        sprices = EC2SpotPrices()

    Returns:
        spot price data (generator)

    """
    def __init__(self, profile='default', start_dt=None, end_dt=None, page_size=500, dt_strings=False, debug=False):
        """
        Args:
            :profile (str):
            :start_dt (datetime): DateTime object marking data collection start
            :end_dt (datetime): DateTime object marking data collection stop
            :pagesize (int):  Number of spot price elements per pagesize
            :debug (bool): debug output toggle
        """
        self.profile = profile
        self.session = boto3.Session(profile_name=self.profile)
        self.regions = get_regions()
        self.start, self.end = self.set_endpoints(start_dt, end_dt)
        self.page_size = page_size
        self.pageconfig = {'PageSize': self.page_size}
        self.dt_strings = dt_strings
        self.debug = debug

    def set_endpoints(self, start_dt=None, end_dt=None, duration=None):
        """
        Rationalize start and end datetimes for data history lookup
        """
        self.de = DurationEndpoints()

        if all(x is None for x in [start_dt, end_dt, duration]):
            return self.de.start, self.de.end

        elif duration and start_dt is None:
            s, e = self.de.default_endpoints(duration_days=duration)

        elif start_dt and end_dt:
            s, e = self.de.custom_endpoints(start_time=start_dt, end_time=end_dt)
        self.start, self.end = s, e    # reset instance variable statics
        return s, e

    def _page_iterators(self, region, page_size=500):
        self.client = self.session.client('ec2', region_name=region)
        self.paginator = self.client.get_paginator('describe_spot_price_history')
        self.page_iterator = self.paginator.paginate(
                                StartTime=self.start,
                                EndTime=self.end,
                                DryRun=self.debug,
                                PaginationConfig={'PageSize': self.page_size})
        return self.page_iterator

    def _region_paginators(self, regions=get_regions()):
        """Supplies regional paginator objects, one per unique AWS region"""
        return [self._page_iterators(region) for region in regions]

    def _spotprice_generator(self, region=None):
        """
        Summary:
            Generator returning up to 1000 data items at once

        Returns:
            spot price data (generator)

        """
        for page_iterator in (self._region_paginators() if region is None else self._region_paginators([region])):
            try:
                for page in page_iterator:
                    for price_dict in page['SpotPriceHistory']:
                        yield utc_conversion(price_dict) if self.dt_strings else price_dict
            except ClientError as e:
                logger.exception(f'Boto client error while downloading spot history data: {e}')
                continue
            except Exception as e:
                logger.exception(f'Unknown exception while calc start & end duration: {e}')

    def generate_pricedata(self, region=None, debug=False):
        """
        Facility when iterating spot price generator method is unavailable
        """
        return {'SpotPriceHistory': [x for x in self._spotprice_generator(region)]}
