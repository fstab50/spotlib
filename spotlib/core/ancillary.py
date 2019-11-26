"""
Summary.

    EC2 SpotPrice Lib, GPL v3 License

    Copyright (c) 2018-2020 Blake Huber

    Python 3 Module Function:  session_selector
        - handles environment-resident credentials utilised
          in deployments such as AWS Lambda.
        - if nothing in the environment, utilises credentials
          tied to a profile_name in the local awscli configuration.

"""

import inspect
import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from spotlib import logger


def session_selector(profile):
    """
        Converts datetime object embedded in a dictionary schema
        to utc datetime string format

    Args:
        :data (list | dict):  list of spot price data.  Alternatively,
            can be same list wrapped in dictionary (below)

    .. code: json

        {
            'AvailabilityZone': 'eu-west-1a',
            'InstanceType': 'm5d.4xlarge',
            'ProductDescription': 'Red Hat Enterprise Linux',
            'SpotPrice': '0.420000',
            'Timestamp': datetime.datetime(2019, 8, 11, 23, 56, 50, tzinfo=tzutc())
        }

    Returns:
        instantiated session, TYPE:  boto3 object

    """
    access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    token = os.environ.get('AWS_SESSION_TOKEN')

    try:
        if access_key and secret_key:
            return boto3.Session(
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    aws_session_token=token
                )

        return boto3.Session(profile_name=profile)

    except ClientError as e:
        fx = inspect.stack()[0][3]
        logger.exception(f'{fx}: Boto client error while downloading spot history data: {e}')

    except NoCredentialsError:
        fx = inspect.stack()[0][3]
        logger.exception(f'{fx}: Unable to authenicate to AWS: No credentials found')
