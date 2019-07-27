import os
import sys
import time
import json
import logging
import pytest
import pdb
import boto3
import moto
from tests import environment


logger = logging.getLogger()
logger.setLevel(logging.INFO)

sys.path.insert(0, os.path.abspath('Code'))
from autotag import index
sys.path.pop(0)


# test module globals
base_path = '/tmp/autotag-tests-%s' % time.time()
version = 'testing-' + base_path
test_assets = 'tests/assets'

# set region default
if os.getenv('AWS_DEFAULT_REGION') is None:
    default_region = 'us-east-2'
    os.environ['AWS_DEFAULT_REGION'] = default_region
else:
    default_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-2')


# target module globals
index.region = default_region
index.ctime = "2017-10-09T10:13:14Z"


ami_id = 'ami-redhat7'
min_count = 1
max_count = 2
ec2_size = 't2.micro'


@moto.mock_ec2
def get_regions():
    ec2 = boto3.client('ec2', region_name=default_region)
    return [x['RegionName'] for x in ec2.describe_regions()['Regions'] if 'cn' not in x['RegionName']]


@pytest.fixture()
def regionize():
    os.environ['AWS_REGION'] = default_region
    yield
    if default_region is not None:
        os.environ['AWS_REGION'] = default_region
    else:
        del os.environ['AWS_REGION']


@pytest.fixture(scope="function")
def create_ec2():
    moto.mock_ec2().start()
    client = boto3.client('ec2', region_name=default_region)
    r = client.run_instances(ImageId=ami_id, MinCount=min_count, MaxCount=min_count)
    instance_id = r['Instances'][0]['InstanceId']
    yield instance_id
    moto.mock_ec2().stop()


@pytest.fixture()
def preapply_tags_snow():
    with open(test_assets + '/preapply_tags_snow.json', 'r') as f1:
        f2 = f1.read()
        content = json.loads(f2)
        yield content


@pytest.fixture()
def return_tags(filename):
    with open(test_assets + '/' + filename, 'r') as f1:
        f2 = f1.read()
        content = json.loads(f2)
        yield content


def add_tooling_tags(account_id, tag_list):
    """
    Add tags for tooling accounts
    """
    if account_id in ('102512488663', '935229214006', '872277419998'):
        special_tags = [
            {
                'Key': 'MPC-AWS-BACKUP',
                'Value': 'CPM'
            },
            {
                'Key': 'cpm backup',
                'Value': 'AtostoolingprBckLinGenDisabled'
            }
        ]
        tag_list.extend(special_tags)
    return tag_list


class TestTagSupport():
    @pytest.mark.parametrize(
        'user, principal, account, account_name, prefix', (
            ('SVC.SNOW', 'AIDAIYRH3XU3AGL7CEO5E', '1777777777777', 'phht-gen-ra1-dev', 'phht'),
            ('A490001', "AIDAIYRH3XU3AGL7CEO5E:A490001", '188888888888', 'acme-gen-ra1-dev', 'atos'),
            ('A490001', "AIDAIYRH3XU3AGL7CEO5E:A490001", '102512488663', 'atos-tooling-dev', 'atos')
            ))
    def test_check_mandatory(self, user, principal, account, account_name, prefix):
        """
        check_mandatory is Autotag module function which
        """
        # set global Autotag-specific vars
        index.user = user
        index.principal = principal
        index.account_prefix = account_name.split('-')[0]
        index.account = account
        index.account_name = account_name
        index.MANDATORY_TAG_PREFIXES = prefix

        if index.account_prefix == 'phht':
            reference_tags = next(return_tags('reference_tags_snow.json'))
        else:
            reference_tags = next(return_tags('reference_tags_atos.json'))

        # add special tags to reference depending upon account
        reference_tags = add_tooling_tags(account, reference_tags)
        r_test = index.check_mandatory(reference_tags)
        # compare
        assert r_test is True

    @pytest.mark.parametrize(
        'user, principal, account, account_name', (
            ('SVC.SNOW', 'AIDAIYRH3XU3AGL7CEO5E', '1777777777777', 'phht-gen-ra1-dev'),
            ('A490001', "AIDAIYRH3XU3AGL7CEO5E:A490001", '188888888888', 'acme-gen-ra1-dev'),
            ('A490001', "AIDAIYRH3XU3AGL7CEO5E:A490001", '102512488663', 'atos-tooling-dev')
            ))
    @moto.mock_ec2
    def test_get_os(self, user, principal, account, account_name):
        """
        Test module func get_os():  returns operating system type of ec2 instance
        """
        # set global Autotag-specific vars
        index.user = user
        index.principal = principal
        index.account = account
        index.account_name = account_name
        # create ec2 instance
        ec2_client = boto3.client('ec2', region_name=default_region)
        r = ec2_client.run_instances(ImageId=ami_id, MinCount=min_count, MaxCount=min_count)
        instance_id = r['Instances'][0]['InstanceId']
        r_test = index.get_ec2_os(instance_id)
        assert r_test == 'linux'

    @pytest.mark.parametrize(
        'user, filter_keys', (
            ('SVC.SNOW',['UHC-SN-BACKUP', 'cpm backup', 'Name']),
            ('A490001', ['MPC-AWS-BACKUP', 'cpm backup']),
            ('A490001', ['MPC-AWS-BACKUP', 'cpm backup'])
            ))
    def test_exclude_tags(self, user, filter_keys):
        """
        Test module func exclude_tags():  removes k,v pairs of tags by
        specified key value
        """
        # set global Autotag-specific vars
        #index.user = user

        # prep tag sets, invoke autotag
        if user == 'SVC.SNOW':
            test_tags = next(return_tags('reference_tags_snow_unfiltered.json'))
            reference_tags = next(return_tags('reference_tags_snow_filtered.json'))
            r_test_tags = index.exclude_tags(test_tags, *filter_keys)
        else:
            test_tags = next(return_tags('reference_tags_iamuser_unfiltered.json'))
            reference_tags = next(return_tags('reference_tags_iamuser_filtered.json'))
            r_test_tags = index.exclude_tags(test_tags, *filter_keys)

        # prepare tag comparisons
        tag_dict = {x['Key']: x['Value'] for x in r_test_tags}
        tag_dict_reference = {x['Key']: x['Value'] for x in reference_tags}
        logger.info('\nAutotag Filtered Tags (tag_dict):')
        logger.info(json.dumps(tag_dict, indent=4))
        logger.info('\nTag Reference (tag_dict_reference):')
        logger.info(json.dumps(tag_dict_reference, indent=4))
        assert tag_dict == tag_dict_reference


class TestManualTagUpdates():
    def test_ec2_tag_operations(self, create_ec2):
        pass
