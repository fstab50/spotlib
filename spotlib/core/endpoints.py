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
import re
import datetime
import inspect
from spotlib.lambda_utils import get_regions, read_env_variable
from spotlib import logger


dt_pattern = re.compile('\d{4}-[01]\d-[0-3]\d[\sT][0-2]\d:[0-5]\d:[0-5]\d(?:\.\d+)?Z?')


class DurationEndpoints():
    """
    Calculates both custom and default endpoints in time which brackets
    the time period for which spot price historical data is retrieved
    """
    def __init__(self, duration_days=1, start_dt=None, end_dt=None, debug=False):
        """

        """
        self.d_days = duration_days

        if all(x is None for x in [start_dt, end_dt]):
            self.start, self.end = self.default_duration_endpoints(self.d_days)

        elif any(x is not None for x in [start_dt, end_dt]):
            x, y = self.calculate_duration_endpoints(start_dt, end_dt)
            self.start = x if x is not None else self.default_duration_endpoints()[0]
            self.end = y if y is not None else self.default_duration_endpoints()[1]

    def default_duration_endpoints(self, duration_days=read_env_variable('default_duration')):
        """
        Supplies the default start and end datetime objects in absence
        of user supplied endpoints which frames time period from which
        to begin and end retrieving spot price data from Amazon APIs.

        Returns:  TYPE: tuple, containing:
            - start (datetime), midnight yesterday
            - end (datetime) midnight, current day

        """
        # end datetime calcs
        dt_date = datetime.datetime.today().date()
        dt_time = datetime.datetime.min.time()
        end = datetime.datetime.combine(dt_date, dt_time)

        # start datetime calcs
        duration = datetime.timedelta(days=duration_days)
        start = end - duration
        return start, end

    def custom_duration_endpoints(self, start_time=None, end_time=None):
        """
            Calculates custom start and end points when given a variety of
            formats including string or None. If both duration_days and start_time,
            end_time values are provided, start and end times will take precedence.

        Args:
            :duration_days (int): Duration between start and end points in 24h days
            :start_time (datetime | str | None):  midnight on provided custom date
            :end_time (datetime | str | None):  midnight on provided custom date

        Returns:
            start, end: points in time, TYPE:  datetime regardless of input format

        """
        try:
            if all(isinstance(x, datetime.datetime) for x in [start_time, end_time]):
                return start, end

            elif any(isinstance(x, str) for x in [start_time, end_time]) \
                and (dt_pattern.match(x) for x in [start_time, end_time]):
                start = self._convert_datetime_string(start_time)
                end = self._convert_datetime_string(end_time)

            elif any(x is None for x in [start_time, end_time]):
                start, end = self.default_duration_endpoints()

        except Exception as e:
            logger.exception(f'Unknown exception while calc start & end duration: {e}')
            sys.exit(exit_codes['E_BADARG']['Code'])
        return  start, end

    def _convert_datetime_string(self, dt_str):
        dt_format = '%Y-%m-%dT%H:%M:%S'
        return datetime.datetime.strptime(dt_str, dt_pattern)
