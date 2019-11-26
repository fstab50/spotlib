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


def authenticated(botosession):
    """
        Tests generic authentication status to AWS Account
        Customised specifically for testing of memory-resident
        credentials stored as environment variables.

    Args:
        :profile (str): iam user name from local awscli configuration

    Returns:
        TYPE: bool, True (Authenticated)| False (Unauthenticated)

    """
    try:

        sts_client = botosession.client('sts')
        httpstatus = sts_client.get_caller_identity()['ResponseMetadata']['HTTPStatusCode']

        if httpstatus.starswith(20):
            # http status code 2XX; successful
            return True

    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidClientTokenId':
            logger.warning(
                '%s: Invalid credentials to authenticate for profile user (%s). Exit. [Code: %d]'
                % (inspect.stack()[0][3], profile, exit_codes['EX_NOPERM']['Code']))

        elif e.response['Error']['Code'] == 'ExpiredToken':
            logger.info(
                '%s: Expired temporary credentials detected for profile user (%s) [Code: %d]'
                % (inspect.stack()[0][3], profile, exit_codes['EX_CONFIG']['Code']))
        else:
            logger.exception(
                '%s: Unknown Boto3 problem. Error: %s' %
                (inspect.stack()[0][3], e.response['Error']['Message']))
    except Exception as e:
        fx = inspect.stack()[0][3]
        logger.exception('{}: Unknown error: {}'.format(fx, e))
    return False


def session_selector(profile='default'):
    """
        Creates a boto3 session object after examining
        available credential set(s).  session selector
        follows the following authenication hierarchy:

            1. Attempts to find memory-resident credentials
               supplied as environment variables (example:
                AWS Lambda service environment)
            2. If (1) fails to find valid credentials, spotlib
               local attempts to utilise awscli credentials
               from local disk.

    Args:
        :profile (str):  Optional awscli profile_name
            corresponding to a set of credentials stored
            in the local awscli configuration

    Returns:
        instantiated session, TYPE:  boto3 object

    """
    access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    token = os.environ.get('AWS_SESSION_TOKEN')

    try:

        if access_key and secret_key:
            session = boto3.Session(
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    aws_session_token=token
                )
            if authenticated(session):
                return session

        return boto3.Session(profile_name=profile)

    except ClientError as e:
        fx = inspect.stack()[0][3]
        logger.exception(f'{fx}: Boto client error while downloading spot history data: {e}')

    except NoCredentialsError:
        fx = inspect.stack()[0][3]
        logger.exception(f'{fx}: Unable to authenicate to AWS: No credentials found')
