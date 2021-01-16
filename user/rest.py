from typing import List
import asyncio
import boto3
import requests
import json
import logging
import os
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key
from aws_lambda_rest_api import RestApi


logger = logging.getLogger()
logger.setLevel('INFO')


AUTH0_DOMAIN = os.environ.get('AUTH0_DOMAIN')
user_url = f'https://{AUTH0_DOMAIN}/api/v2/users'
AUTH0_ACCESS_TOKEN_ARN = os.environ.get('AUTH0_ACCESS_TOKEN_ARN')

lambda_client = boto3.client('lambda')


class UserApi(RestApi):
    detail_key = 'user_id'
    default_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,X-Amz-Security-Token,Authorization,X-Api-Key,X-Requested-With,Accept,Access-Control-Allow-Methods,Access-Control-Allow-Origin,Access-Control-Allow-Headers",
        "X-Requested-With": "*"
    }

    def list(self, event, context):
        user_ids: List[str] = json.loads(
            event['queryStringParameters']['user_ids'])

        token_res = lambda_client.invoke(
            FunctionName=AUTH0_ACCESS_TOKEN_ARN, InvocationType='RequestResponse')
        token = json.loads(token_res['Payload'].read().decode())
        headers = {'authorization': f'Bearer {token}'}
        users = []
        for user_id in user_ids:
            res = requests.get(f'{user_url}/{user_id}', headers=headers)
            users.append(json.loads(res.text))

        return {
            'statusCode': 200,
            'body': json.dumps(users),
        }


class UserSearchApi(RestApi):
    default_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,X-Amz-Security-Token,Authorization,X-Api-Key,X-Requested-With,Accept,Access-Control-Allow-Methods,Access-Control-Allow-Origin,Access-Control-Allow-Headers",
        "X-Requested-With": "*"
    }

    def list(self, event, context):
        email: str = event['queryStringParameters']['email']
        query = f'email:*{email}*'
        token_res = lambda_client.invoke(
            FunctionName=AUTH0_ACCESS_TOKEN_ARN, InvocationType='RequestResponse')
        token = json.loads(token_res['Payload'].read().decode())
        headers = {'authorization': f'Bearer {token}'}
        url = f'{user_url}?q={query}'
        res = requests.get(url, headers=headers)
        return {'statusCode': 200, 'body': res.text}


lambda_handler = UserApi().create_handler()
search_handler = UserSearchApi().create_handler()
