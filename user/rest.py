from typing import List
import boto3
import requests
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


AUTH0_DOMAIN = os.environ.get('AUTH0_DOMAIN')
user_url = f'https://{AUTH0_DOMAIN}/api/v2/users'
AUTH0_API_CLIENT_ID = os.environ.get('AUTH0_API_CLIENT_ID')
AUTH0_API_CLIENT_SECRET = os.environ.get('AUTH0_API_CLIENT_SECRET')

# parameter_table_name = os.environ.get('PARAMETER_TABLE_NAME')
# parameter_table = boto3.resource('dynamodb').Table(parameter_table_name)


payload = {
    'client_id': AUTH0_API_CLIENT_ID,
    'client_secret': AUTH0_API_CLIENT_SECRET,
    'grant_type': 'client_credentials',
}


class UserApi(RestApi):
    detail_key = 'user_id'
    default_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,X-Amz-Security-Token,Authorization,X-Api-Key,X-Requested-With,Accept,Access-Control-Allow-Methods,Access-Control-Allow-Origin,Access-Control-Allow-Headers",
        "X-Requested-With": "*"
    }

    def list(self, event, context):
        user_ids: List[str] = event['queryStringParameters']['user_ids']
        token = get_access_token()
        headers = {'authorization': f'Bearer {token}'}
        users = []
        for user_id in user_ids:
            res = requests.get(f'{user_url}/{user_id}', headers=headers)
            users.append(json.loads(res.text))

        return {
            'statusCode': 200,
            'body': json.dumps(users),
        }


def get_access_token():
    headers = {'content-type': 'application/json'}
    url = f'https://{AUTH0_DOMAIN}/oauth/token'
    audience = f'https://{AUTH0_DOMAIN}/api/v2/'
    payload = {
        'client_id': AUTH0_API_CLIENT_ID,
        'client_secret': AUTH0_API_CLIENT_SECRET,
        'audience': audience,
        'grant_type': 'client_credentials',
    }
    res = requests.post(url, headers=headers, data=json.dumps(payload))
    return json.loads(res.text)['access_token']


lambda_handler = UserApi().create_handler()
