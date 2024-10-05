import boto3
import json
import os
from jira import JIRA

import logging
logger = logging.getLogger()
logger.setLevel("INFO")


def findings_notifier(finding):
    jira_basic_auth_email = os.getenv("Jira_basicAuth_email")
    jira_basic_auth_api_token = os.getenv("Jira_basicAuth_apiToken")
    jira_server_url = os.getenv("Jira_serverUrl")
    jira_project_key = os.getenv("Jira_projectKey")

    #Jira connection
    jira_connection = JIRA(
        basic_auth=(jira_basic_auth_email, jira_basic_auth_api_token),
        server=jira_server_url
    )
    jira_dict = {
        'project': {'key': jira_project_key},
        'summary': finding['Title'],
        'description':  f'{finding['Resources']}',
        'issuetype': {'name': 'Bug'}
    }
    new_issue = jira_connection.create_issue(fields=jira_dict)
    logger.info(f'new_issue: {new_issue}')

def lambda_handler(event, context):

    region = os.getenv("SECURITY_HUB_REGION",os.getenv("AWS_DEFAULT_REGION"))

    env_variables_regions = os.getenv("REGIONS",os.getenv("AWS_DEFAULT_REGION"))
    regions = [item for item in env_variables_regions.split(",") if item]

    env_variables_accounts = os.getenv("ACCOUNTS",os.getenv("AWS_DEFAULT_ACCOUNT"))
    accounts = [item for item in env_variables_accounts.split(",") if item]

    logger.info(f'env_variables_securityhub_region: {region}, regions: {regions}, accounts: {accounts}')

    client = (boto3.session.Session(region_name=region)).client('securityhub')

    for accountId in accounts:
        filters = {
            'AwsAccountId': [{'Value': accountId, 'Comparison': 'EQUALS'}],
            'ProductName': [{'Value': 'Inspector', 'Comparison': 'EQUALS'}],
            'RecordState': [{'Value': 'ACTIVE', 'Comparison': 'EQUALS'}],
            'WorkflowStatus': [{'Value': 'NEW', 'Comparison': 'EQUALS'}],
            'FindingProviderFieldsSeverityLabel': [{'Value': 'CRITICAL', 'Comparison': 'EQUALS'}],
            'VulnerabilitiesFixAvailable': [{'Value': 'YES', 'Comparison': 'EQUALS'}]
            }

        pages = client.get_paginator('get_findings').paginate(Filters=filters, PaginationConfig={'MaxItems': 1})

        try:
            for page in pages:
                for finding in page['Findings']:
                    logger.info(finding)
                    findings_notifier(finding)
                    response = client.batch_update_findings(
                            FindingIdentifiers=[
                                {
                                    "Id": finding['Id'],
                                    "ProductArn": finding['ProductArn'],
                                },
                            ],
                            Workflow={
                                'Status': 'NOTIFIED',
                            },
                        )
                    logger.info(response)
                    for processed_findings in response["ProcessedFindings"]:
                        logger.info(
                            f"processed and suppressed id {processed_findings['Id']} productarn {processed_findings['ProductArn']}"
                        )

                    for unprocessed_findings in response["UnprocessedFindings"]:
                        logger.error(
                            f"unprocessed finding id {unprocessed_findings['FindingIdentifier']['Id']} productarn {unprocessed_findings['FindingIdentifier']['ProductArn']} error code {unprocessed_findings['ErrorCode']} error message {unprocessed_findings['ErrorMessage']}"
                        )                    
                    
        except Exception as e:
            logger.error(f"Error {e}")
