import boto3
import decimal
import json
import logging
import os
import uuid
from aws_lambda_rest_api import RestApi
from boto3.dynamodb.conditions import Attr, Key


logger = logging.getLogger()
logger.setLevel('INFO')

project_table_name = os.environ.get('PROJECT_TABLE_NAME')
project_table = boto3.resource('dynamodb').Table(project_table_name)

project_user_table_name = os.environ.get('PROJECT_USER_TABLE_NAME')
project_user_table = boto3.resource('dynamodb').Table(project_user_table_name)


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
        params = {'primaryKey': f'User#{user_id}'}
        user_projects_data = project_user_table.get_item(Key=params)
        project_ids = user_projects_data.get('Item', [])
        projects = project_table.scan(FilterExpression=Attr('projectId').is_in(project_ids))

        return {
            'statusCode': 200,
            'body': json.dumps(projects['Items']),
        }

    def retrieve(self, event, context):
        project_id = event['pathParameters'].get('project_id')
        params = {'projectId': project_id}
        project = project_table.get_item(Key=params)['Item']

        return {'statusCode': 200, 'body': json.dumps(project)}

    def create(self, event, context):
        project_id = str(uuid.uuid4())
        project_data = {**json.loads(event['body']), 'projectId': project_id}
        project_table.put_item(Item=project_data)

        params = {'projectId': project_id}
        project = project_table.get_item(Key=params)['Item']

        return {'statusCode': 200, 'body': json.dumps(project)}

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
