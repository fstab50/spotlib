"""
Summary.

    Python 3 Class performing datatime object --> utc formatted string

"""

import datetime

def utc_conversion(data):
    dt = data['Timestamp'].strftime('%Y-%m-%dT%H:%M:%SZ')
    data['Timestamp'] = dt
    return data


class UtcConversion():
    def __init__(self, data):
        self.d = data['SpotPriceHistory'] if isinstance(data, dict) else data
        self.formatted = [x['Timestamp'].strftime('%Y-%m-%dT%H:%M:%SZ') for x in self.d]
        self.prices = self.convert(self.d)

    def convert(self, pricelist):
        for index, pdict in enumerate(pricelist):
            pricelist[index]['Timestamp'] = self.formatted[index]
        return pricelist
