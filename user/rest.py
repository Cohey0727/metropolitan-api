from typing import List
import boto3
import http.client
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
user_url = f'/{AUTH0_DOMAIN}/api/v2/users'
AUTH0_API_CLIENT_ID = os.environ.get('AUTH0_API_CLIENT_ID')
AUTH0_API_CLIENT_SECRET = os.environ.get('AUTH0_API_CLIENT_SECRET')

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
        emails: List[str] = event['pathParameters']['emails']
        email_qs = 'email:("' + '" OR "'.join(emails) + '")'
        conn = http.client.HTTPSConnection("")
        conn.request(
            'GET', f'${user_url}?q={email_qs}&search_engine=v3', headers=headers
        )
        res = conn.getresponse()
        data = res.read()
        print(data.decode("utf-8"))
        return {
            'statusCode': 200,
            'body': 'success',
        }


lambda_handler = UserApi().create_handler()
