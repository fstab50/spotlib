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

sys.path.insert(0, os.path.abspath('Code'))
from autotag import index
from autotag.audit_ec2 import dns_hostname
sys.path.pop(0)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
def resource_objects(region=default_region):
    moto.mock_ec2().start()
    client = boto3.client('ec2', region_name=region)
    rsc = boto3.resource('ec2', region_name=region)
    yield client, rsc
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


def save_tags(tags):
    """ Save tag dictionary to disk """
    filename = 'save-tags.json'
    with open(filename, 'w') as f1:
        f1(json.dumps(tags, indent=4))
    if os.path.isfile(filename):
        return True
    return False


def extract_tag(tag_list, key):
    """
    Summary:
        Search tag list for prescence of tag matching key parameter
    Returns:
        tag, TYPE: list
    """
    if {x['Key']: x['Value'] for x in tag_list}.get(key):
        return list(filter(lambda x: x['Key'] == key, tag_list))[0]
    return []


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


def return_reference_dict(id, ref_tags, pre_tags):
    """
    Summary: Inserts Name tag if required
    Returns:
        tag_dictionary, TYPE: dict
    """
    ref_dict = {x['Key']: x['Value'] for x in ref_tags}
    hostname = dns_hostname(id)
    if {x['Key']: x['Value'] for x in pre_tags}.get('UHC-SN-NAME'):
        ref_dict['Name'] = {x['Key']: x['Value'] for x in pre_tags}.get('UHC-SN-NAME')
    elif {x['Key']: x['Value'] for x in pre_tags}.get('Name'):
        ref_dict['Name'] = {x['Key']: x['Value'] for x in pre_tags}.get('Name')
    else:
        ref_dict['Name'] = hostname
    return ref_dict


class TestInstances():
    """
    Notes:
        Parameter sets for IAM.USER A468001 must be added back into pytest.mark.parameterize
        set when a solution is found for Autotag failing to add ANY TAGS when invoked
        during an active testing session from this module.

        Cause is still unknown, but possibly related to calling index.module functions
        independently of lambda_handler() func.
    """
    @pytest.mark.parametrize('resource_type', (('volume'), ('instance'), ('eni')))
    @pytest.mark.parametrize(
        'user, principal, account, account_name', (
            ('SVC.SNOW', 'AIDAIYRH3XU3AGL7CEO5E', '1777777777777', 'test-gen-ra1-dev'),
            ('SVC.SNOW', "AIDAIYRH3XU3AGL7CEO5E", '188888888888', 'test-gen-ra1-pr'),
            ('SVC.SNOW', "AIDAIYRH3XU3AGL7CEO5E", '102512488663', 'atos-tooling-dev'),
            ('A490001', "AIDAIYRH3XU3AGL7CEO5E:A490001", '765512488663', 'atos-gen-ra1-pr'),
            ('A490001', "AIDAIYRH3XU3AGL7CEO5E:A490001", '102512488663', 'atos-tooling-dev')
            ))
    @moto.mock_ec2
    def test_1_run_ec2_instances(self, user, principal, account, account_name, resource_type):
        # set global Autotag-specific vars
        index.user = user
        index.principal = principal
        index.account_id = account
        index.account_name = account_name

        # create ec2 machine
        ec2_client = boto3.client('ec2', region_name=default_region)
        ec2 = boto3.resource('ec2', region_name=default_region)
        r = ec2_client.run_instances(ImageId=ami_id, MinCount=min_count, MaxCount=min_count)

        instance_id = r['Instances'][0]['InstanceId']

        if resource_type == 'instance':
            resource_id = instance_id
            reference_file_snow = 'test1_tags_snow_instance.json'
            reference_file_iamuser = 'test1_tags_iamuser.json'
        elif resource_type == 'volume':
            resource_id = ec2_client.describe_volumes()['Volumes'][0]['Attachments'][0]['VolumeId']
            reference_file_snow = 'test1_tags_snow_vol.json'
            reference_file_iamuser = 'reference_tags_iamuser_filtered_vol.json'
        else:
            resource_id = r['Instances'][0]['NetworkInterfaces'][0]['NetworkInterfaceId']
            reference_file_snow = 'test1_tags_snow_eni.json'
            reference_file_iamuser = 'reference_tags_iamuser_filtered_eni.json'

        if index.user == 'SVC.SNOW':
            # apply servicenow tags
            preapply_tags = next(preapply_tags_snow())
            ec2.create_tags(Resources=[instance_id], Tags=preapply_tags)
            reference_tags = next(return_tags(reference_file_snow))
        else:
            # Apply Name tag to instance
            preapply_tags = [{'Key': 'Name', 'Value': 'EC2TEST0001'}]
            ec2.create_tags(Resources=[instance_id], Tags=preapply_tags)
            reference_tags = next(return_tags(reference_file_iamuser))
            # add special tags to reference depending upon account
            if resource_type == 'instance':
                reference_tags = add_tooling_tags(account, reference_tags)

        # setup detail object
        detail = {
            "userIdentity": {
                "userName": user
            },
            "requestParameters": {
              "resourcesSet": {
                "items": [
                  {
                    "resourceId": instance_id
                  }
                ]
              },
            },
            "responseElements": {
                "instancesSet": {
                    "items": [
                        {"instanceId": instance_id}
                    ]
                }
            }
        }
        # invoke Autotag module func
        r_test = index.run_ec2_instances(detail)
        logger.info('run_ec2_instances lambda response:  %s' % str(r_test))
        r = ec2_client.describe_tags(
            Filters=[{
                        'Name': 'resource-id',
                        'Values': [resource_id],
                    },
                ]
            )
        # prepare tag comparisons
        tag_dict = {x['Key']: x['Value'] for x in r['Tags']}
        tag_dict_reference = return_reference_dict(instance_id, reference_tags, preapply_tags)
        # logging
        logger.info('\nTags Applied to EC2 %s (tag_dict):' % resource_type)
        logger.info(json.dumps(tag_dict, indent=4))
        logger.info('\nTag Reference (tag_dict_reference):')
        logger.info(json.dumps(tag_dict_reference, indent=4))
        # compare
        assert tag_dict == tag_dict_reference


class TestNameTags():
    """
    Notes:
        - run_ec2_instances module Function Tests
        - variations of Name tag on instances, volumes, and eni's.
    """
    @pytest.mark.parametrize('resource_type', (('volume'), ('instance'), ('eni')))
    @pytest.mark.parametrize(
        'user, principal, account, account_name', (
            ('SVC.SNOW', 'AIDAIYRH3XU3AGL7CEO5E', '1777777777777', 'test-gen-ra1-dev'),
            ('SVC.SNOW', "AIDAIYRH3XU3AGL7CEO5E", '188888888888', 'test-gen-ra1-pr'),
            ('A490001', "AIDAIYRH3XU3AGL7CEO5E:A490001", '765512488663', 'atos-gen-ra1-pr'),
            ('A490001', "AIDAIYRH3XU3AGL7CEO5E:A490001", '102512488663', 'atos-tooling-dev')
            ))
    @moto.mock_ec2
    def test_2_run_ec2_instances_NameTags(self, user, principal, account, account_name, resource_type):
        # set global Autotag-specific vars
        index.user = user
        index.principal = principal
        index.account_id = account
        index.account_name = account_name

        # create ec2 machine
        ec2_client = boto3.client('ec2', region_name=default_region)
        ec2 = boto3.resource('ec2', region_name=default_region)
        r = ec2_client.run_instances(ImageId=ami_id, MinCount=min_count, MaxCount=min_count)

        instance_id = r['Instances'][0]['InstanceId']

        if resource_type == 'instance':
            resource_id = instance_id
            reference_file_snow = 'test2_tags_snow_instance.json'
            reference_file_iamuser = 'test2_tags_iamuser_instance.json'
        elif resource_type == 'volume':
            resource_id = ec2_client.describe_volumes()['Volumes'][0]['Attachments'][0]['VolumeId']
            reference_file_snow = 'test2_tags_snow_vol.json'
            reference_file_iamuser = 'test2_tags_iamuser_vol.json'
        else:
            resource_id = r['Instances'][0]['NetworkInterfaces'][0]['NetworkInterfaceId']
            reference_file_snow = 'test2_tags_snow_eni.json'
            reference_file_iamuser = 'test2_tags_iamuser_eni.json'

        if index.user == 'SVC.SNOW':
            # apply servicenow tags
            preapply_tags = next(return_tags('test2_tags_snow_instance.json'))
            ec2.create_tags(Resources=[instance_id], Tags=preapply_tags)
            reference_tags = next(return_tags(reference_file_snow))
        else:
            preapply_tags = []
            reference_tags = next(return_tags(reference_file_iamuser))
            # add special tags to reference depending upon account
            if resource_type == 'instance':
                reference_tags = add_tooling_tags(account, reference_tags)

        # setup detail object
        detail = {
            "userIdentity": {
                "userName": user
            },
            "requestParameters": {
              "resourcesSet": {
                "items": [
                  {
                    "resourceId": instance_id
                  }
                ]
              }
            },
            "responseElements": {
                "instancesSet": {
                    "items": [
                        {"instanceId": instance_id}
                    ]
                }
            }
        }
        # invoke Autotag module func
        r_test = index.run_ec2_instances(detail)
        logger.info('run_ec2_instances lambda response:  %s' % str(r_test))
        r = ec2_client.describe_tags(
            Filters=[{
                        'Name': 'resource-id',
                        'Values': [resource_id],
                    },
                ]
            )
        # prepare tag comparisons
        tag_dict = {x['Key']: x['Value'] for x in r['Tags']}
        tag_dict_reference = return_reference_dict(instance_id, reference_tags, preapply_tags)
        # logging
        logger.info('\nTags Applied to EC2 %s (tag_dict):' % resource_type)
        logger.info(json.dumps(tag_dict, indent=4))
        logger.info('\nTag Reference (tag_dict_reference):')
        logger.info(json.dumps(tag_dict_reference, indent=4))
        # compare
        assert tag_dict == tag_dict_reference


class TestEC2Volumes():
    @pytest.mark.parametrize(
    'user, principal, account, account_name', (
            ('SVC.SNOW', 'AIDAIYRH3XU3AGL7CEO5E', '1777777777777', 'test-gen-ra1-dev'),
            ('A490001', "AIDAIYRH3XU3AGL7CEO5E:A490001", '188888888888', 'test-gen-ra1-dev')
            ))
    @moto.mock_ec2
    def test_3_create_ec2_volume(self, user, principal, account, account_name, resource_objects):
        # set global Autotag-specific vars
        index.user = user
        index.principal = principal
        index.account_id = account
        index.account_name = account_name
        # get clients
        ec2_client, ec2 = resource_objects

        # create volume
        vol_id = ec2_client.create_volume(
            AvailabilityZone=default_region + 'a',
            Size=10,
            VolumeType='gp2')['VolumeId']
        # create snapshots
        snapshot_id = ec2_client.create_snapshot(VolumeId=vol_id)['SnapshotId']

        # apply source tags to source resource, build ref tagset
        if index.user == 'SVC.SNOW':
            ec2.create_tags(Resources=[snapshot_id], Tags=next(return_tags('reference_tags_snow_filtered.json')))
            reference_tags = next(return_tags('reference_tags_snow_filtered.json'))
        else:
            ec2.create_tags(Resources=[snapshot_id], Tags=next(return_tags('reference_tags_iamuser_filtered.json')))
            reference_tags = next(return_tags('reference_tags_iamuser_filtered.json'))

        # setup detail object
        detail = {
            "requestParameters": {"snapshotId": snapshot_id},
            "responseElements": {"volumeId": vol_id}
        }
        # invoke Autotag module func
        r_test = index.create_ec2_volume(detail)
        r = ec2_client.describe_tags(
            Filters=[{
                        'Name': 'resource-id',
                        'Values': [vol_id],
                    },
                ]
            )
        # prepare tag comparisons
        tag_dict = {x['Key']: x['Value'] for x in r['Tags']}
        tag_dict_reference = {x['Key']: x['Value'] for x in reference_tags}
        logger.info('\nTags Applied to volume (tag_dict):')
        logger.info(json.dumps(tag_dict, indent=4))
        logger.info('\nTag Reference (tag_dict_reference):')
        logger.info(json.dumps(tag_dict_reference, indent=4))
        # compare
        assert tag_dict == tag_dict_reference

    @pytest.mark.parametrize(
        'user, principal, account, account_name', (
            ('SVC.SNOW', 'AIDAIYRH3XU3AGL7CEO5E', '1777777777777', 'test-gen-ra1-dev'),
            ('A490001', "AIDAIYRH3XU3AGL7CEO5E:A490001", '188888888888', 'test-gen-ra1-dev'),
            ('A490001', 'AIDAIYRH3XU3AGL7CEO5E:A490001', '102512488663', 'atos-tooling-dev')
            ))
    @moto.mock_ec2
    def test_4_attach_ec2_volume(self, user, principal, account, account_name, resource_objects):
        # set global Autotag-specific vars
        index.user = user
        index.principal = principal
        index.account_id = account
        index.account_name = account_name
        # get clients
        ec2_client, ec2 = resource_objects

        # create
        r = ec2_client.run_instances(ImageId=ami_id, MinCount=min_count, MaxCount=min_count)
        instance_id = r['Instances'][0]['InstanceId']
        az = r['Instances'][0]['Placement']['AvailabilityZone']

        # build ref tagset
        if index.user == 'SVC.SNOW':
            # apply servicenow tags
            preapply_tags = next(return_tags('reference_tags_snow_unfiltered.json'))
            ec2.create_tags(Resources=[instance_id], Tags=preapply_tags)
            reference_tags = next(return_tags('test4_reference_tags_snow.json'))
        else:
            preapply_tags = []
            # Apply Name tag to instance
            preapply_tags = add_tooling_tags(account, preapply_tags)
            ec2.create_tags(Resources=[instance_id], Tags=preapply_tags)
            reference_tags = next(return_tags('test4_reference_tags_iamuser.json'))

        # create volume
        r_cv = ec2_client.create_volume(
            AvailabilityZone=az,
            Size=10,
            VolumeType='gp2'
        )
        vol_id = r_cv['VolumeId']
        r_attach = ec2_client.attach_volume(
            Device='xvdb',
            InstanceId=instance_id,
            VolumeId=vol_id
            )

        # setup detail object
        detail = {
            "requestParameters": {"instanceId": instance_id},
            "responseElements": {"volumeId": vol_id}
        }
        # invoke Autotag module func
        r_test = index.attach_ec2_volume(detail)
        r = ec2_client.describe_tags(
            Filters=[{
                        'Name': 'resource-id',
                        'Values': [vol_id],
                    },
                ]
            )
        # prepare tag comparisons
        tag_dict = {x['Key']: x['Value'] for x in r['Tags']}
        tag_dict_reference = return_reference_dict(instance_id, reference_tags, preapply_tags)
        logger.info('\nTags Applied to volume (tag_dict):')
        logger.info(json.dumps(tag_dict, indent=4))
        logger.info('\nTag Reference (tag_dict_reference):')
        logger.info(json.dumps(tag_dict_reference, indent=4))
        # compare
        assert tag_dict == tag_dict_reference

    @pytest.mark.parametrize(
        'user, usertype, principal, account, account_name', (
            ('SVC.SNOW', 'snow', 'AIDAIYRH3XU3AGL7CEO5E', '1777777777777', 'test-gen-ra1-dev'),
            ('A490001', 'iamuser', 'AIDAIYRH3XU3AGL7CEO5E:A490001', '188888888888', 'test-gen-ra1-dev'),
            ('A490001', 'iamuser', 'AIDAIYRH3XU3AGL7CEO5E:A490001', '102512488663', 'atos-tooling-dev')
            ))
    @moto.mock_ec2
    def test_5_attach_ec2_volume_preapply(self, user, usertype, principal, account, account_name, resource_objects):
        """
        Preapply tags to volume prior to attach to EC2 Instance
        """
        # set global Autotag-specific vars
        index.user = user
        index.principal = principal
        index.account_id = account
        index.account_name = account_name
        # get clients
        ec2_client, ec2 = resource_objects

        # create
        r = ec2_client.run_instances(ImageId=ami_id, MinCount=min_count, MaxCount=min_count)
        instance_id = r['Instances'][0]['InstanceId']
        az = r['Instances'][0]['Placement']['AvailabilityZone']

        # build ref tagset
        if index.user == 'SVC.SNOW':
            # apply servicenow tags to instance
            preapply_tags = next(return_tags('reference_tags_snow_unfiltered.json'))
            ec2.create_tags(Resources=[instance_id], Tags=preapply_tags)
            reference_tags = next(return_tags('test5_reference_tags_snow.json'))
        else:
            # Apply Name tag to instance
            preapply_tags = add_tooling_tags(account, [{'Key': 'Name', 'Value': 'EC2TEST0001'}])
            ec2.create_tags(Resources=[instance_id], Tags=preapply_tags)
            reference_tags = next(return_tags('test5_reference_tags_iamuser.json'))

        # create volume
        r_cv = ec2_client.create_volume(
            AvailabilityZone=az,
            Size=10,
            VolumeType='gp2'
        )
        # preapply tags
        vol_id = r_cv['VolumeId']
        preapply_tags_volume = 'test5_preapply_tags_volume_%s.json' % usertype
        ec2.create_tags(Resources=[vol_id], Tags=next(return_tags(preapply_tags_volume)))

        r_attach = ec2_client.attach_volume(
            Device='xvdb',
            InstanceId=instance_id,
            VolumeId=vol_id
            )

        # setup detail object
        detail = {
            "requestParameters": {"instanceId": instance_id},
            "responseElements": {"volumeId": vol_id}
        }
        # invoke Autotag module func
        r_test = index.attach_ec2_volume(detail)
        r = ec2_client.describe_tags(
            Filters=[{
                        'Name': 'resource-id',
                        'Values': [vol_id],
                    },
                ]
            )
        # prepare tag comparisons
        tag_dict = {x['Key']: x['Value'] for x in r['Tags']}
        tag_dict_reference = return_reference_dict(instance_id, reference_tags, preapply_tags)
        logger.info('\nTags Applied to volume (tag_dict):')
        logger.info(json.dumps(tag_dict, indent=4))
        logger.info('\nTag Reference (tag_dict_reference):')
        logger.info(json.dumps(tag_dict_reference, indent=4))
        # compare
        assert tag_dict == tag_dict_reference


class TestEC2Images():
    @pytest.mark.parametrize(
        'user, principal, account, account_name', (
            ('SVC.SNOW', 'AIDAIYRH3XU3AGL7CEO5E', '1777777777777', 'test-gen-ra1-dev'),
            ('A490001', "AIDAIYRH3XU3AGL7CEO5E:A490001", '188888888888', 'test-gen-ra1-dev')
            ))
    @moto.mock_ec2
    def test_6_create_ec2_image(self, user, principal, account, account_name, resource_objects):
        # set global Autotag-specific vars
        index.user = user
        index.principal = principal
        index.account_id = account
        index.account_name = account_name
        # get clients
        ec2_client, ec2 = resource_objects

        # create instance
        instance_id = ec2_client.run_instances(
            ImageId=ami_id,
            MinCount=min_count, MaxCount=min_count)['Instances'][0]['InstanceId']

        # create image
        image_id = ec2_client.create_image(InstanceId=instance_id, Name='mytest-image')['ImageId']

        # apply source tags to source resource, build ref tagset
        if index.user == 'SVC.SNOW':
            ec2.create_tags(Resources=[instance_id], Tags=next(return_tags('reference_tags_snow_filtered.json')))
            reference_tags = next(return_tags('reference_tags_snow_filtered.json'))
        else:
            ec2.create_tags(Resources=[instance_id], Tags=next(return_tags('reference_tags_iamuser_filtered.json')))
            reference_tags = next(return_tags('reference_tags_iamuser_filtered.json'))

        # setup detail object
        detail = {
            "requestParameters": {"instanceId": instance_id},
            "responseElements": {"imageId": image_id}
        }
        # invoke Autotag module func
        r_test = index.create_ec2_image(detail)
        r = ec2_client.describe_tags(
            Filters=[{
                        'Name': 'resource-id',
                        'Values': [image_id],
                    },
                ]
            )
        # prepare tag comparisons
        tag_dict = {x['Key']: x['Value'] for x in r['Tags']}
        tag_dict_reference = {x['Key']: x['Value'] for x in reference_tags}
        logger.info('\nTags Applied to Image (tag_dict):')
        logger.info(json.dumps(tag_dict, indent=4))
        logger.info('\nTag Reference (tag_dict_reference):')
        logger.info(json.dumps(tag_dict_reference, indent=4))
        # compare
        assert tag_dict == tag_dict_reference

    @pytest.mark.parametrize(
        'user, principal, account, account_name', (
            ('SVC.SNOW', 'AIDAIYRH3XU3AGL7CEO5E', '1777777777777', 'test-gen-ra1-dev'),
            ('A490001', "AIDAIYRH3XU3AGL7CEO5E:A490001", '188888888888', 'test-gen-ra1-dev')
            ))
    @moto.mock_ec2
    def test_7_copy_ec2_image(self, user, principal, account, account_name, resource_objects):
        # set global Autotag-specific vars
        index.user = user
        index.principal = principal
        index.account_id = account
        index.account_name = account_name
        # get clients
        ec2_client, ec2 = resource_objects
        # create instance
        instance_id = ec2_client.run_instances(
            ImageId=ami_id,
            MinCount=min_count, MaxCount=min_count)['Instances'][0]['InstanceId']

        # create image
        image_id = ec2_client.create_image(InstanceId=instance_id, Name='mytest-image')['ImageId']

        # apply source tags to source resource, build ref tagset
        if index.user == 'SVC.SNOW':
            ec2.create_tags(Resources=[image_id], Tags=next(return_tags('reference_tags_snow_filtered.json')))
            reference_tags = next(return_tags('reference_tags_snow_filtered.json'))
        else:
            ec2.create_tags(Resources=[image_id], Tags=next(return_tags('reference_tags_iamuser_filtered.json')))
            reference_tags = next(return_tags('reference_tags_iamuser_filtered.json'))

        # copy image to us-east-1 region
        use1_client = boto3.client('ec2', region_name='us-east-1')
        image_copied = use1_client.copy_image(
            Description='remote image copy',
            Name='RMIC',
            SourceImageId=image_id,
            SourceRegion=default_region)['ImageId']

        # setup detail object
        detail = {
            "requestParameters": {
                "sourceImageId": image_id,
                "sourceRegion": default_region
            },
            "responseElements": {"imageId": image_copied}
        }
        # invoke Autotag module func
        r_test = index.copy_ec2_image(detail)
        # retrieve copy of tags on target resource
        r = ec2_client.describe_tags(
            Filters=[{
                        'Name': 'resource-id',
                        'Values': [image_id],
                    },
                ]
            )
        # prepare tag comparisons
        tag_dict = {x['Key']: x['Value'] for x in r['Tags']}
        tag_dict_reference = {x['Key']: x['Value'] for x in reference_tags}
        logger.info('\nTags Applied to Copied Image (tag_dict):')
        logger.info(json.dumps(tag_dict, indent=4))
        logger.info('\nTag Reference (tag_dict_reference):')
        logger.info(json.dumps(tag_dict_reference, indent=4))
        # compare
        assert tag_dict == tag_dict_reference


class TestEC2Snapshots():
    @pytest.mark.parametrize(
        'user, usertype, principal, account, account_name', (
            ('SVC.SNOW', 'snow', 'AIDAIYRH3XU3AGL7CEO5E', '1777777777777', 'test-gen-ra1-dev'),
            ('A490001', 'iamuser', 'AIDAIYRH3XU3AGL7CEO5E:A490001', '188888888888', 'test-gen-ra1-dev')
            ))
    @moto.mock_ec2
    def test_8_create_ec2_snapshot(self, user, usertype, principal, account, account_name, resource_objects):
        # set global Autotag-specific vars
        index.user = user
        index.principal = principal
        index.account_id = account
        index.account_name = account_name
        # get clients
        ec2_client, ec2 = resource_objects

        # create source instance
        r = ec2_client.run_instances(ImageId=ami_id, MinCount=min_count, MaxCount=min_count)
        instance_id = r['Instances'][0]['InstanceId']
        az = r['Instances'][0]['Placement']['AvailabilityZone']

        # create volume
        r_cv = ec2_client.create_volume(
                AvailabilityZone=az,
                Size=10,
                VolumeType='gp2'
            )
        vol_id = r_cv['VolumeId']
        r_attach = ec2_client.attach_volume(
            Device='xvdb',
            InstanceId=instance_id,
            VolumeId=vol_id
            )
        # preapply tags
        vol_id = r_cv['VolumeId']
        preapply_tags = next(return_tags('test8_preapply_tags_volume_%s.json' % usertype))
        ec2.create_tags(Resources=[vol_id], Tags=preapply_tags)

        # create snapshot
        snapshot = ec2.create_snapshot(Description='test8 snapshot creation', VolumeId=vol_id)

        # build ref tagset
        reference_tags = next(return_tags('test8_reference_tags_%s.json' % usertype))

        # setup detail object
        detail = {
            "requestParameters": {"volumeId": vol_id},
            "responseElements": {"snapshotId": snapshot.id}
        }

        # invoke Autotag module func
        r_test = index.create_ec2_snapshot(detail)
        r = ec2_client.describe_tags(
            Filters=[{
                        'Name': 'resource-id',
                        'Values': [snapshot.id],
                    },
                ]
            )
        # prepare tag comparisons
        tag_dict = {x['Key']: x['Value'] for x in r['Tags']}
        tag_dict_reference = return_reference_dict(instance_id, reference_tags, preapply_tags)
        logger.info('\nTags Applied to Image (tag_dict):')
        logger.info(json.dumps(tag_dict, indent=4))
        logger.info('\nTag Reference (tag_dict_reference):')
        logger.info(json.dumps(tag_dict_reference, indent=4))
        # compare
        assert tag_dict == tag_dict_reference
