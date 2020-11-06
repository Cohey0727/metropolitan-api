import boto3
import json
import logging
import os
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel('INFO')

table_name = os.environ.get('TABLE_NAME')
connection_talble = boto3.resource('dynamodb').Table(table_name)

def lambda_handler(event, context):
    connection_id = event['requestContext'].get('connectionId')
    res = connection_talble.scan(FilterExpression=Key('connectionId').eq(connection_id))

    with connection_talble.batch_writer(overwrite_by_pkeys=['projectId', 'connectionId']) as batch:
        for coneetionRecord in res['Items']:
            project_id = coneetionRecord['projectId']
            batch.delete_item(Key={'projectId': project_id, 'connectionId': connection_id})

    return {'statusCode': 200, 'body': 'Disconnected.'}
