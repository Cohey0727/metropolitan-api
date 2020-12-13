import boto3
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

    for connection_record in res['Items']:
        project_id = connection_record['projectId']
        connection_talble.delete_item(Key={'projectId': project_id, 'connectionId': connection_id})

    return {'statusCode': 200, 'body': 'Disconnected.'}
