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


class UserProjectApi(RestApi):
    detail_key = 'project_id'
    default_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,X-Amz-Security-Token,Authorization,X-Api-Key,X-Requested-With,Accept,Access-Control-Allow-Methods,Access-Control-Allow-Origin,Access-Control-Allow-Headers",
        "X-Requested-With": "*"
    }

    def update(self, event, context):
        user_id = event['pathParameters'].get('user_id')
        project_id = event['pathParameters'].get('project_id')
        project_data = project_table.query(
            KeyConditionExpression=Key('projectId').eq(project_id)
        )
        projects = project_data['Items']
        return {
            'statusCode': 200,
            'body': json.dumps(projects),
        }

    def destroy(self, event, context):
        project_id = event['pathParameters'].get('project_id')
        project_data = project_table.query(
            KeyConditionExpression=Key('projectId').eq(project_id)
        )
        projects = project_data['Items']
        return {
            'statusCode': 200,
            'body': json.dumps(projects),
        }


lambda_handler = UserProjectApi().create_handler()
