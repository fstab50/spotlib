"""
Summary.

    Python 3 Class performing datatime object --> utc formatted string

"""

import datetime


def utc_conversion(data):
    """
        Converts datetime object embedded in a dictionary schema
        to utc datetime string format

    Returns:
        datetime, TYPE: str
    """
    dt = data['Timestamp'].strftime('%Y-%m-%dT%H:%M:%SZ')
    data['Timestamp'] = dt
    return data


class UtcConversion():
    """
    Class for converting datetime objects embedded in boto3
    spot price output dictionary schema
    """
    def __init__(self, data):
        self.d = data['SpotPriceHistory'] if isinstance(data, dict) else data
        self.formatted = [x['Timestamp'].strftime('%Y-%m-%dT%H:%M:%SZ') for x in self.d]
        self.prices = self.convert(self.d)

    def convert(self, pricelist):
        """
            Converts datetime object embedded in a dictionary schema
            to utc datetime string format

        Args:
            :pricelist (list): list of spot price dictionaries
                with time represented as a datetime object

        Returns:
            list of dictionaries, TYPE: list
        """
        for index, pdict in enumerate(pricelist):
            pricelist[index]['Timestamp'] = self.formatted[index]
        return pricelist
