
import os
import boto3
from botocore.exceptions import ClientError
from spotlib.lambda_utils import get_regions
from spotlib.core import EC2SpotPrices

import boto3, json, datetime
from spotlib.core import EC2SpotPrices
from libtools import logger

os.environ['S3_BUCKET'] = 'spotprices-dev'
os.environ['duration_days'] = '1'
os.environ['page_size'] = '500'



#days = 7
d = EC2SpotPrices()
start, end = d.start, d.end

def test_spotprice_pull():
    for region in get_regions():

        global s3_fname
        s3_fname = '_'.join(
                        [
                            start.strftime('%Y-%m-%dT%H:%M:%S'),
                            end.strftime('%Y-%m-%dT%H:%M:%S'),
                            'all-instance-spot-prices.json'
                        ]
                    )

        prices = [x for x in d.spotprice_generator(region, False)]

        # build unique collection of instances for this region
        instances = list(set([x['InstanceType'] for x in prices]))
        instances.sort()

        # spot price data destination
        bucket = 'aws01-storage'
        s3object = prices
        key = os.path.join(region, s3_fname)
        profile = 'gcreds-da'

        _completed = s3upload(bucket, s3object, key, profile)
        success = f'Successful write to s3 bucket {bucket} of object {key}'
        failure = f'Problem writing data to s3 bucket {bucket} of object {key}'
        logger.info(success) if _completed else logger.waring(failure)

        # instance types list destination
        bucket = 'aws01-storage'
        s3object = instances
        key = os.path.join(region, 'spot-instanceTypes')

        if s3upload(bucket, s3object, key, profile):
            print(True and _completed)

        failure = f'Problem writing data to s3 bucket {bucket} of object {key}'
        logger.warning(failure)
