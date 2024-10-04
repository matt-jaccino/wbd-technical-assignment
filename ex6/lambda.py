import botocore
import boto3
import json
import datetime
from botocore.exceptions import ClientError


# Helper function used to validate input
def check_defined(reference, reference_name):
    if not reference:
        raise Exception('Error: ', reference_name, 'is not defined')
    return reference


# Check whether the message is OversizedConfigurationItemChangeNotification or not
def is_oversized_changed_notification(message_type):
    check_defined(message_type, 'messageType')
    return message_type == 'OversizedConfigurationItemChangeNotification'


# Get configurationItem using getResourceConfigHistory API
# in case of OversizedConfigurationItemChangeNotification
def get_configuration(resource_type, resource_id, configuration_capture_time, config):
    result = config.get_resource_config_history(
        resourceType=resource_type,
        resourceId=resource_id,
        laterTime=configuration_capture_time,
        limit=1)
    configurationItem = result['configurationItems'][0]
    return convert_api_configuration(configurationItem)


# Convert from the API model to the original invocation model
def convert_api_configuration(configurationItem):
    for k, v in configurationItem.items():
        if isinstance(v, datetime.datetime):
            configurationItem[k] = str(v)
    configurationItem['awsAccountId'] = configurationItem['accountId']
    configurationItem['ARN'] = configurationItem['arn']
    configurationItem['configurationStateMd5Hash'] = configurationItem['configurationItemMD5Hash']
    configurationItem['configurationItemVersion'] = configurationItem['version']
    configurationItem['configuration'] = json.loads(configurationItem['configuration'])
    if 'relationships' in configurationItem:
        for i in range(len(configurationItem['relationships'])):
            configurationItem['relationships'][i]['name'] = configurationItem['relationships'][i]['relationshipName']
    return configurationItem


# Based on the type of message get the configuration item
# either from configurationItem in the invoking event
# or using the getResourceConfigHistory API in getConfiguration function.
def get_configuration_item(invokingEvent: dict, config: boto3.client):
    check_defined(invokingEvent, 'invokingEvent')
    if is_oversized_changed_notification(invokingEvent['messageType']):
        configurationItemSummary = check_defined(invokingEvent['configurationItemSummary'], 'configurationItemSummary')
        return get_configuration(
            configurationItemSummary['resourceType'],
            configurationItemSummary['resourceId'],
            configurationItemSummary['configurationItemCaptureTime'],
            config
        )
    return check_defined(invokingEvent['configurationItem'], 'configurationItem')


# Check whether the resource has been deleted. If it has, then the evaluation is unnecessary.
def is_applicable(configurationItem, event):
    try:
        check_defined(configurationItem, 'configurationItem')
        check_defined(event, 'event')
    except:
        return True
    status = configurationItem['configurationItemStatus']
    eventLeftScope = event['eventLeftScope']
    if status == 'ResourceDeleted':
        print("Resource Deleted, setting Compliance Status to NOT_APPLICABLE.")
    return (status == 'OK' or status == 'ResourceDiscovered') and not eventLeftScope


#### END BOILERPLATE NONSENSE ####


def bucket_is_public(bucket: str, s3: boto3.client) -> bool:
    try:
        resp = s3.get_public_access_block(Bucket=bucket)

    except ClientError as exc:
        print(
            f"Unable to get public access block for '{bucket}': {exc}"
        )
        print("Erring on the side of caution")

        return True

    else:
        return all(block for block in resp.get('PublicAccessBlockConfiguration', {}).values())


def bucket_block_public_access(bucket: str, s3: boto3.client):
    try:
        s3.put_public_access_block(
            Bucket=bucket,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
    except ClientError as exc:
        print(
            f"Unable to set public access block for '{bucket}': {exc}"
        )
        raise exc


def evaluate_change_notification_compliance(configuration_item, rule_parameters):
    check_defined(configuration_item, 'configuration_item')
    check_defined(configuration_item['configuration'], 'configuration_item[\'configuration\']')
    if rule_parameters:
        check_defined(rule_parameters, 'rule_parameters')

    if (configuration_item['resourceType'] != 'AWS::S3::Bucket'):
        return 'NOT_APPLICABLE'

    allowed_public_tag = json.loads(rule_parameters['tag'])

    bucket = configuration_item['resourceId']

    s3 = boto3.client('s3')

    if not bucket_is_public(bucket, s3):
        return 'COMPLIANT'

    # if it is public, make sure the 
    if all(tag in configuration_item.get('tags', {}).items() for tag in allowed_public_tag.items()):
        return 'COMPLIANT'

    ## Normally, I would have this just function as an actual Config rule and have a separate Lambda trigger off of
    ## an EventBridge rule looking for NON_COMPLIANT evals, but I'm just going to combine the two here

    try:
        bucket_block_public_access(bucket, s3)

    except ClientError as exc:
        print(f"Failed to remediate: {exc}")

        print("Remediation failed. Flag the bucket.")
        return 'NON_COMPLIANT'

    return 'COMPLIANT'



#### RESUME BOILERPLATE ####


def lambda_handler(event, context):
    invoking_event = json.loads(event['invokingEvent'])

    rule_parameters = json.loads(event.get('ruleParameters', r"{}"))

    compliance_value = 'NOT_APPLICABLE'

    config = boto3.client('config')

    configuration_item = get_configuration_item(invoking_event, config)

    if is_applicable(configuration_item, event):
        compliance_value = evaluate_change_notification_compliance(
            configuration_item,
            rule_parameters
        )

    config.put_evaluations(
        Evaluations=[
            {
                'ComplianceResourceType': invoking_event['configurationItem']['resourceType'],
                'ComplianceResourceId': invoking_event['configurationItem']['resourceId'],
                'ComplianceType': compliance_value,
                'OrderingTimestamp': invoking_event['configurationItem']['configurationItemCaptureTime']
            },
        ],
        ResultToken=event['resultToken']
    )
