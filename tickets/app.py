import boto3
import json
import logging
import os
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel('INFO')

table_name = os.environ.get('TABLE_NAME')
ticket_talble = boto3.resource('dynamodb').Table(table_name)


def lambda_handler(event, context):
    project_id = event['queryStringParameters'].get('project_id')
    logger.info(f'TalbeName: {table_name}, projectId: {project_id}')
    ticket_data = ticket_talble.query(
        KeyConditionExpression=Key('projectId').eq(project_id)
    )

    return {
        'statusCode': 200,
        'body': json.dumps(ticket_data['Items']),
    }
