import boto3
import requests
import json
import logging
import os
from shortuuid import uuid
from aws_lambda_rest_api import RestApi
from boto3.dynamodb.conditions import Attr, Key

logger = logging.getLogger()
logger.setLevel('INFO')


AUTH0_DOMAIN = os.environ.get('AUTH0_DOMAIN')
AUTH0_ACCESS_TOKEN_ARN = os.environ.get('AUTH0_ACCESS_TOKEN_ARN')

project_table_name = os.environ.get('PROJECT_TABLE_NAME')
project_table = boto3.resource('dynamodb').Table(project_table_name)

lambda_client = boto3.client('lambda')


def get_default_project():
    board_id1 = uuid()
    board_id2 = uuid()
    return {
        'boards': [
            {
                'boardId': board_id1,
                'title': 'Backlog',
                'description': 'Backlog Board',
                'lists': [
                    {'listId': uuid(), 'title': 'Draft'},
                    {'listId': uuid(), 'title': 'In Progress'},
                    {'listId': uuid(), 'title': 'Review'},
                    {'listId': uuid(), 'title': 'Finish'}
                ]
            },
            {
                'boardId': board_id2,
                'title': 'Development',
                'description': 'Development Board',
                'lists': [
                    {'listId': uuid(), 'title': 'Draft'},
                    {'listId': uuid(), 'title': 'In Progress'},
                    {'listId': uuid(), 'title': 'Review'},
                    {'listId': uuid(), 'title': 'Finish'}
                ]
            }
        ],
        'flow': [
            {'input': board_id2, 'output': board_id1}
        ]
    }


class ProjectApi(RestApi):
    detail_key = 'project_id'
    default_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,X-Amz-Security-Token,Authorization,X-Api-Key,X-Requested-With,Accept,Access-Control-Allow-Methods,Access-Control-Allow-Origin,Access-Control-Allow-Headers",
        "X-Requested-With": "*"
    }

    def list(self, event, context):
        user_id = event['queryStringParameters'].get('user_id')
        url = f'https://{AUTH0_DOMAIN}/api/v2/users/{user_id}/roles'
        token_res = lambda_client.invoke(
            FunctionName=AUTH0_ACCESS_TOKEN_ARN, InvocationType='RequestResponse')
        token = json.loads(token_res['Payload'].read().decode())
        headers = {'authorization': f'Bearer {token}'}
        res = requests.get(url, headers=headers)
        roles = json.loads(res.text)

        project_ids = [
            role['name'].split(':')[1] for role in roles if role['name'].split(':')[0] == 'project'
        ]

        projects = []
        if project_ids:
            res = project_table.scan(FilterExpression=Attr(
                'projectId').is_in(project_ids))
            projects = res['Items']

        return {'statusCode': 200, 'body': json.dumps(projects)}

    def retrieve(self, event, context):
        project_id = event['pathParameters'].get('project_id')
        params = {'projectId': project_id}
        project = project_table.get_item(Key=params)['Item']

        return {'statusCode': 200, 'body': json.dumps(project)}

    def create(self, event, context):
        # create project
        project_id = uuid()
        new_project = {**get_default_project(), **
                       json.loads(event['body']), 'projectId': project_id}
        project_table.put_item(Item=new_project)

        # prepare meta
        token_res = lambda_client.invoke(
            FunctionName=AUTH0_ACCESS_TOKEN_ARN, InvocationType='RequestResponse')
        token = json.loads(token_res['Payload'].read().decode())
        headers = {'authorization': f'Bearer {token}'}

        # create role
        title = new_project['title']
        body = {
            'name': f'project:{project_id}',
            'description': f'Member of project "{title}"',
        }
        role_url = f'https://{AUTH0_DOMAIN}/api/v2/roles'
        res = requests.post(role_url, json=body, headers=headers)
        role = json.loads(res.text)

        # assign role
        role_data = {'users': [new_project["author"]]}
        role_user_url = f'https://{AUTH0_DOMAIN}/api/v2/roles/{role["id"]}/users'
        res = requests.post(role_user_url, json=role_data, headers=headers)

        return {'statusCode': 200, 'body': json.dumps(new_project)}

    def update(self, event, context):
        project_id = event['pathParameters'].get('project_id')
        project_data = json.loads(event['body'])
        project_data.pop('projectId', None)

        update_expression = 'SET '
        expression_values = {}
        expression_names = {}

        for key, value in project_data.items():
            update_expression += f' #{key} = :{key},'
            expression_values[f':{key}'] = value
            expression_names[f'#{key}'] = key

        update_expression = update_expression[:-1]

        response = project_table.update_item(
            Key={'projectId': project_id},
            ExpressionAttributeNames=expression_names,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues='UPDATED_NEW'
        )

        return {
            'statusCode': 200,
            'body': json.dumps(response['Attributes'])
        }

    def destory(self, event, context):
        project_id = event['pathParameters'].get('project_id')
        params = {'projectId': project_id}
        project_table.delete_item(Key=params)
        return {'statusCode': 200, 'body': json.dumps(params)}


lambda_handler = ProjectApi().create_handler()
