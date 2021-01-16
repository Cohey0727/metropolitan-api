import boto3
import requests
import json
import logging
import os
from boto3.dynamodb.conditions import Key
from aws_lambda_rest_api import RestApi


logger = logging.getLogger()
logger.setLevel('INFO')

AUTH0_DOMAIN = os.environ.get('AUTH0_DOMAIN')
AUTH0_ACCESS_TOKEN_ARN = os.environ.get('AUTH0_ACCESS_TOKEN_ARN')

project_table_name = os.environ.get('PROJECT_TABLE_NAME')
project_table = boto3.resource('dynamodb').Table(project_table_name)

lambda_client = boto3.client('lambda')


class ProjectUserApi(RestApi):
    detail_key = 'user_id'
    default_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,X-Amz-Security-Token,Authorization,X-Api-Key,X-Requested-With,Accept,Access-Control-Allow-Methods,Access-Control-Allow-Origin,Access-Control-Allow-Headers",
        "X-Requested-With": "*"
    }

    def list(self, event, context):
        project_id = event['pathParameters'].get('project_id')
        params = {'projectId': project_id}
        project = project_table.get_item(Key=params)['Item']
        role_id = project['roleId']
        url = f'https://{AUTH0_DOMAIN}/api/v2/roles/{role_id}/users'
        token_res = lambda_client.invoke(
            FunctionName=AUTH0_ACCESS_TOKEN_ARN, InvocationType='RequestResponse')
        token = json.loads(token_res['Payload'].read().decode())
        headers = {'authorization': f'Bearer {token}'}
        res = requests.get(url, headers=headers)
        return {'statusCode': 200, 'body': res.text}

    def create(self, event, context):
        project_id = event['pathParameters'].get('project_id')
        params = {'projectId': project_id}
        project = project_table.get_item(Key=params)['Item']
        role_id = project['roleId']

        body = json.loads(event['body'])
        user_id = body['user_id']
        params = {'users': [user_id]}
        token_res = lambda_client.invoke(
            FunctionName=AUTH0_ACCESS_TOKEN_ARN, InvocationType='RequestResponse')
        token = json.loads(token_res['Payload'].read().decode())
        headers = {'authorization': f'Bearer {token}'}

        url = f'https://{AUTH0_DOMAIN}/api/v2/roles/{role_id}/users'
        data = {'users': [user_id]}
        res = requests.post(url, json=data, headers=headers)
        return {'statusCode': res.status_code, 'body': json.dumps({'message': 'success'})}

    def destroy(self, event, context):
        project_id = event['pathParameters']['project_id']
        user_id = event['pathParameters']['user_id']

        params = {'projectId': project_id}
        project = project_table.get_item(Key=params)['Item']
        role_id = project['roleId']
        params = {'users': [user_id]}
        token_res = lambda_client.invoke(
            FunctionName=AUTH0_ACCESS_TOKEN_ARN, InvocationType='RequestResponse')
        token = json.loads(token_res['Payload'].read().decode())
        headers = {'authorization': f'Bearer {token}'}

        url = f'https://{AUTH0_DOMAIN}/api/v2/users/{user_id}/roles'
        data = {'roles': [role_id]}
        requests.delete(url, data=data, headers=headers)


lambda_handler = ProjectUserApi().create_handler()
