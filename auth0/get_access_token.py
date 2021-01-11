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
AUTH0_API_CLIENT_ID = os.environ.get('AUTH0_API_CLIENT_ID')
AUTH0_API_CLIENT_SECRET = os.environ.get('AUTH0_API_CLIENT_SECRET')

parameter_table_name = os.environ.get('PARAMETER_TABLE_NAME')
parameter_table = boto3.resource('dynamodb').Table(parameter_table_name)


def lambda_handler(*args, **kwargs):
    params = {'parameterKey': 'Auth0AccessToken'}
    access_token_data = parameter_table.get_item(Key=params).get('Item')
    if access_token_data is not None:
        return access_token_data['value']

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
    access_token = json.loads(res.text)['access_token']
    datetime_now = datetime.now()
    ttl_time = datetime_now + timedelta(days=1)
    ttl = int(ttl_time.timestamp())
    access_token_data = {**params, 'value': access_token, 'ttl': ttl}
    parameter_table.put_item(Item=access_token_data)
    return access_token
