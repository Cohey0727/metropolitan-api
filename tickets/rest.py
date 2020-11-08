import boto3
import decimal
import json
import logging
import os
import re
import uuid
from boto3.dynamodb.conditions import Key
from aws_lambda_rest_api import RestApi


logger = logging.getLogger()
logger.setLevel('INFO')

table_name = os.environ.get('TABLE_NAME')
ticket_talble = boto3.resource('dynamodb').Table(table_name)


def deserialize_ticket(data: dict) -> dict:
    position = data['currentPosition']
    res = {
        **data,
        'currentPosition': f'board#{position["board"]}::list#{position["list"]}',
        'order': decimal.Decimal(str(data['order']))
    }
    return res


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


class TicketApi(RestApi):
    detail_key = 'ticket_id'

    def list(self, event, context):
        project_id = event['pathParameters'].get('project_id')
        ticket_data = ticket_talble.query(
            KeyConditionExpression=Key('projectId').eq(project_id)
        )
        tickets = ticket_data['Items']
        res = [serialize_ticket(ticket) for ticket in tickets]
        return {
            'statusCode': 200,
            'body': json.dumps(res),
        }

    def create(self, event, context):
        project_id = event['pathParameters'].get('project_id')
        ticket_data = deserialize_ticket(json.loads(event['body']))
        ticket_id = str(uuid.uuid4())
        ticket_talble.put_item(
            Item={
                **ticket_data,
                'projectId': project_id,
                'ticketId': ticket_id,
            },
        )

        response = ticket_talble.query(
            KeyConditionExpression=Key('projectId').eq(project_id) & Key('ticketId').eq(ticket_id)
        )['Items'][0]

        return {
            'statusCode': 200,
            'body': json.dumps(serialize_ticket(response))
        }

    def update(self, event, context):
        project_id = event['pathParameters'].get('project_id')
        ticket_id = event['pathParameters'].get('ticket_id')

        ticket_data = deserialize_ticket(json.loads(event['body']))
        ticket_data.pop('ticketId', None)
        ticket_data.pop('projectId', None)

        update_expression = 'SET '
        expression_values = {}
        expression_names = {}
        for key, value in ticket_data.items():
            update_expression += f' #{key} = :{key},'
            expression_values[f':{key}'] = value
            expression_names[f'#{key}'] = key

        update_expression = update_expression[:-1]

        response = ticket_talble.update_item(
            Key={'projectId': project_id, 'ticketId': ticket_id},
            ExpressionAttributeNames=expression_names,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues='UPDATED_NEW'
        )

        return {
            'statusCode': 200,
            'body': json.dumps(serialize_ticket(response['Attributes']))
        }

    def destory(self, event, context):
        project_id = event['pathParameters'].get('project_id')
        ticket_id = event['pathParameters'].get('ticket_id')
        ticket_talble.delete_item(
            Key={'projectId': project_id, 'ticketId': ticket_id},
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'projectId': project_id, 'ticketId': ticket_id}),
        }


lambda_handler = TicketApi().create_handler()
