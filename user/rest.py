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

project_table_name = os.environ.get('PROJECT_TABLE_NAME')
project_table = boto3.resource('dynamodb').Table(project_table_name)

project_user_table_name = os.environ.get('PROJECT_USER_TABLE_NAME')
project_user_table = boto3.resource('dynamodb').Table(project_user_table_name)


class UserApi(RestApi):
    detail_key = 'user_id'
    default_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,X-Amz-Security-Token,Authorization,X-Api-Key,X-Requested-With,Accept,Access-Control-Allow-Methods,Access-Control-Allow-Origin,Access-Control-Allow-Headers",
        "X-Requested-With": "*"
    }

    def list(self, event, context):
        return {
            'statusCode': 200,
            'body': 'success',
        }


lambda_handler = UserApi().create_handler()
