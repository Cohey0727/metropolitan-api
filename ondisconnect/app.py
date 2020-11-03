import boto3
from boto3.dynamodb.conditions import Key
import json
import logging
import os

logger = logging.getLogger()
logger.setLevel('INFO')

table_name = os.environ.get('TABLE_NAME')
connection_talble = boto3.resource('dynamodb')


def lambda_handler(event, context):
    project_id = event['queryStringParameters'].get('project_id')
    connection_id = event['requestContext'].get('connectionId')
    logger.info(f'TalbeName: {table_name}, projectId: {project_id}')
    connection_talble.delete(Key={'projectId': project_id, 'connectionId': connection_id})
    return {"statusCode": 200, "body": "Connected."}
