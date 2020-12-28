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
project_user_table_name = os.environ.get('PROJECT_USER_TABLE_NAME')
project_user_table = boto3.resource('dynamodb').Table(project_user_table_name)


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
        project_data = project_user_table.query(
            IndexName='projectIdIndex',
            KeyConditionExpression=Key('type').eq('Member')
            & Key('projectId').eq(project_id)
        )
        project_users = project_data['Items']
        user_ids = [project_user['userId'] for project_user in project_users]
        params = {'user_ids': json.dumps(user_ids)}
        res = requests.get(user_api_url, params=params)
        return {'statusCode': 200, 'body': res.text}


lambda_handler = ProjectUserApi().create_handler()
