import boto3
import json
import logging
import os
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel('INFO')

connetion_table_name = os.environ.get('CONNETION_TABLE_NAME')
connection_talble = boto3.resource('dynamodb').Table(connetion_table_name)

ticket_table_name = os.environ.get('TICKET_TABLE_NAME')
ticket_talble = boto3.resource('dynamodb').Table(ticket_table_name)

ws_endpoint = os.environ.get('WS_ENDPOINT')
tickets_ws = boto3.client('apigatewaymanagementapi', endpoint_url=ws_endpoint)


def lambda_handler(event, context):

    records = event['Records']
    project_ids = set(record['dynamodb']['NewImage']
                      ['projectId']['S'] for record in records)

    with connection_talble.batch_writer(overwrite_by_pkeys=['projectId', 'connectionId']) as batch:
        for project_id in project_ids:
            progate_project_tickets(project_id, batch)

    return {'statusCode': 200, 'body': 'Data sent.'}


def progate_project_tickets(project_id: int, batch):
    ticket_data = ticket_talble.query(
        KeyConditionExpression=Key('projectId').eq(project_id)
    )

    connection_data = connection_talble.query(
        KeyConditionExpression=Key('projectId').eq(project_id)
    )

    for coneetion_record in connection_data['Items']:
        connection_id = coneetion_record['connectionId']
        try:
            tickets_ws.post_to_connetion(
                Data=json.dumps(ticket_data),
                ConnectionId=connection_id
            )
        except:
            batch.delete_item(
                Key={'projectId': project_id, 'connectionId': connection_id})
