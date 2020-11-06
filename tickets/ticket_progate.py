import boto3
import json
import logging
import os
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel('INFO')

connetion_table_name = os.environ.get('CONNETION_TABLE_NAME')
ticket_table_name = os.environ.get('TICKET_TABLE_NAME')
connetion_talble = boto3.resource('dynamodb').Table(connetion_table_name)
ticket_talble = boto3.resource('dynamodb').Table(ticket_table_name)


def lambda_handler(event, context):
    project_id = event['queryStringParameters'].get('project_id')
    logger.info(f'TalbeName: {table_name}, projectId: {project_id}')
    ticket_data = ticket_talble.query(
        KeyConditionExpression=Key('projectId').eq(project_id)
    )

    return {
        "statusCode": 200,
        "body": json.dumps(ticket_data),
    }
