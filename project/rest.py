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
        project_ids = user_projects_data.get('Item', {}).get('values')

        projects = []
        if project_ids:
            res = project_table.scan(
                FilterExpression=Attr('projectId').is_in(project_ids))
            projects = res['Items']

        return {'statusCode': 200, 'body': json.dumps(projects)}

    def retrieve(self, event, context):
        project_id = event['pathParameters'].get('project_id')
        params = {'projectId': project_id}
        project = project_table.get_item(Key=params)['Item']

        return {'statusCode': 200, 'body': json.dumps(project)}

    def create(self, event, context):
        project_id = str(uuid.uuid4())
        new_project = {**json.loads(event['body']), 'projectId': project_id}
        project_table.put_item(Item=new_project)

        user_project_key = {'primaryKey': f'User#{new_project["author"]}'}
        user_projects = project_user_table \
            .get_item(Key=user_project_key) \
            .get('Item', None)

        if user_projects:
            new_project_ids = [*user_projects['values'], project_id]
            new_user_projects_data = {'values': new_project_ids}
            update_expression = 'SET '
            expression_values = {}
            expression_names = {}
            for key, value in new_user_projects_data.items():
                update_expression += f' #{key} = :{key},'
                expression_values[f':{key}'] = value
                expression_names[f'#{key}'] = key

            update_expression = update_expression[:-1]

            project_user_table.update_item(
                Key=user_project_key,
                ExpressionAttributeNames=expression_names,
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
            )
        else:
            new_user_projects_data = {**user_project_key, 'values': [project_id]}
            project_table.put_item(Item=new_user_projects_data)

        return {'statusCode': 200, 'body': json.dumps(new_project)}

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
