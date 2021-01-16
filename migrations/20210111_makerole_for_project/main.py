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
AUTH0_ACCESS_TOKEN_ARN = os.environ.get('AUTH0_ACCESS_TOKEN_ARN')
project_table_name = os.environ.get('PROJECT_TABLE_NAME')
project_table = boto3.resource('dynamodb').Table(project_table_name)


def main():
    lambda_client = boto3.client('lambda')
    token_res = lambda_client.invoke(
        FunctionName=AUTH0_ACCESS_TOKEN_ARN, InvocationType='RequestResponse')
    token = json.loads(token_res['Payload'].read().decode())
    projects = project_table.scan()['Items']
    with project_table.batch_writer(overwrite_by_pkeys=['projectId']) as batch:
        for project in projects:
            role = create_project_role(project, token)
            project['roleId'] = role['id']
            batch.put_item(Item=project)


def create_project_role(project, token):
    project_id = project['projectId']
    title = project['title']
    body = {
        'name': f'project:{project_id}',
        'description': f'Member of project "{title}"',
    }
    role_url = f'https://{AUTH0_DOMAIN}/api/v2/roles'
    headers = {'authorization': f'Bearer {token}'}
    res = requests.post(role_url, body, headers=headers)
    return json.loads(res.text)


if __name__ == "__main__":
    main()
