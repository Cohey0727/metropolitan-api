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
role_user_url = '/api/v2/roles/{role_id}/users'

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
        url = role_user_url.format(role_id=role_id)
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

        url = role_user_url.format(role_id=role_id)
        data = {'users': [user_id]}
        requests.post(url, data, headers=headers)

        return {'statusCode': 200, 'body': json.dumps({'message': 'success'})}


lambda_handler = ProjectUserApi().create_handler()
