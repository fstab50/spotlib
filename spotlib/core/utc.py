"""
Summary.

    Python 3 Class performing datatime object --> utc formatted string

"""

import datetime

def utc_conversion(data):
    d = data['SpotPriceHistory'] if isinstance(data, dict) else data
    for index, dt in enumerate([x['Timestamp'].strftime('%Y-%m-%dT%H:%M:%SZ') for x in d]):
        pdict = d[index]
        pdict['Timestamp'] = dt
        d[index] = pdict
    return {'SpotPriceHistory': d}


class UtcConversion():
    def __init__(self, data):
        self.d = data['SpotPriceHistory'] if isinstance(data, dict) else data
        self.formatted = [x['Timestamp'].strftime('%Y-%m-%dT%H:%M:%SZ') for x in self.d]
        self.prices = self.convert(self.d)

    def convert(self, pricelist):
        for index, pdict in enumerate(pricelist):
            pricelist[index]['Timestamp'] = self.formatted[index]
        return pricelist
