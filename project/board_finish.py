import boto3
import requests
import json
import logging
import os
from boto3.dynamodb.conditions import Key
from aws_lambda_rest_api import RestApi


logger = logging.getLogger()
logger.setLevel('INFO')

user_api_url = os.environ.get('USER_API_URL')
project_table_name = os.environ.get('PROJECT_TABLE_NAME')
project_table = boto3.resource('dynamodb').Table(project_table_name)
ticket_table_name = os.environ.get('TICKET_TABLE_NAME')
ticket_table = boto3.resource('dynamodb').Table(ticket_table_name)


def create_position_str(board_id, list_id):
    return f'board#{board_id}::list#{list_id}'


class BoardFinishApi(RestApi):
    default_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,X-Amz-Security-Token,Authorization,X-Api-Key,X-Requested-With,Accept,Access-Control-Allow-Methods,Access-Control-Allow-Origin,Access-Control-Allow-Headers",
        "X-Requested-With": "*"
    }

    def create(self, event, context):
        project_id = event['pathParameters'].get('project_id')
        board_id = event['pathParameters'].get('board_id')

        params = {'projectId': project_id}
        project = project_table.get_item(Key=params)['Item']

        boards = project['boards']
        board = next(
            filter(lambda board: board['boardId'] == board_id, boards), None)
        list_id = board['lists'][-1]['listId']

        source_position = create_position_str(board_id, list_id)
        target_tickets = ticket_table.query(
            IndexName='currentPositionIndex',
            KeyConditionExpression=Key('projectId').eq(project_id)
            & Key('currentPosition').eq(source_position)
        )['Items']

        flow = project['flow']
        link = (link for link in flow if link['output'] == board_id)
        next_board_id = link['input']
        next_board = next(
            filter(lambda board: board['boardId'] == next_board_id, boards), None)

        destination_position = 'board#Completed::list#Completed'

        if next_board:
            next_list_id = next_board['lists'][-1]['listId']
            destination_position = create_position_str(
                next_board_id, next_list_id)

        for ticket in target_tickets:
            ticket['currentPosition'] = destination_position

        with ticket_table.batch_writer(overwrite_by_pkeys=['projectId', 'ticketId']) as batch:
            [batch.put_item(Item=ticket) for ticket in target_tickets]

        return {'statusCode': 200, 'body': json.dumps({'message': 'success'})}


lambda_handler = BoardFinishApi().create_handler()


"""
# Sample Code For Command Line
project_id='BVZ3zPkAmxsevAQgqvqhFQ'
source_position='board#W7w63E2vQ3q2rn7Wxeiseb::list#nJ8byCBCQeQGcb8VnBq7om'
target_tickets=ticket_table.query(IndexName='currentPositionIndex', KeyConditionExpression=Key('projectId').eq(project_id) & Key('currentPosition').eq(source_position))['Items']

for ticket in target_tickets:
    ticket['currentPosition'] = 'board#W7w63E2vQ3q2rn7Wxeiseb::list#nJ8byCBCQeQGcb8VnBq7om'

with ticket_table.batch_writer(overwrite_by_pkeys=['projectId', 'ticketId']) as batch:
    [batch.put_item(Item=ticket) for ticket in target_tickets]

"""
