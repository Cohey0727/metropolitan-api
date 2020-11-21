import boto3
import json
import logging
import os
import re
from typing import List, Any, Dict
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel('INFO')

connection_table_name = os.environ.get('CONNECTION_TABLE_NAME')
connection_talble = boto3.resource('dynamodb').Table(connection_table_name)

ticket_table_name = os.environ.get('TICKET_TABLE_NAME')
ticket_talble = boto3.resource('dynamodb').Table(ticket_table_name)

ws_endpoint = os.environ.get('WS_ENDPOINT')
tickets_ws = boto3.client('apigatewaymanagementapi', endpoint_url=ws_endpoint)


border_regex = re.compile(r'(?<=board#)([a-zA-Z0-9]|\-)+')
ticket_regex = re.compile(r'(?<=list#)([a-zA-Z0-9]|\-)+')


def serialize_ticket(data: dict) -> dict:
    position: str = data['currentPosition']
    order = data['order']

    res = {
        **data,
        'order': float(order),
        'currentPosition': {
            'board': border_regex.search(position).group(0),
            'list': ticket_regex.search(position).group(0),
        },
    }
    return res


def lambda_handler(event, context):
    records = event['Records']
    project_ids = set(record['dynamodb']['Keys']
                      ['projectId']['S'] for record in records)

    with connection_talble.batch_writer(overwrite_by_pkeys=['projectId', 'connectionId']) as batch:
        for project_id in project_ids:
            progate_project_tickets(project_id, batch)

    return {'statusCode': 200, 'body': 'Data sent.'}


def progate_project_tickets(project_id: int, batch):
    tickets = ticket_talble.query(
        KeyConditionExpression=Key('projectId').eq(project_id)
    )

    connection_data = connection_talble.query(
        KeyConditionExpression=Key('projectId').eq(project_id)
    )
    ticket_data = [serialize_ticket(ticket) for ticket in tickets['Items']]

    for connection_record in connection_data['Items']:
        connection_id = connection_record['connectionId']
        try:
            tickets_ws.post_to_connection(
                Data=json.dumps(ticket_data),
                ConnectionId=connection_id
            )
        except Exception as e:
            logger.error(e)
            batch.delete_item(
                Key={'projectId': project_id, 'connectionId': connection_id}
            )
