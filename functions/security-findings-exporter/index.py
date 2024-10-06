import boto3
import json
import os
from jira import JIRA
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def findings_notifier(jira_connection, finding, jira_project_key):
    # Response can be found in https://docs.aws.amazon.com/securityhub/1.0/APIReference/API_AwsSecurityFinding.html

    # defails of JIRA rest can be found in https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-post

    # https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/
    jira_dict = {
        'project': {'key': jira_project_key},
        'summary': finding['Title'],

        "description": {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "heading",
                    "attrs": {
                        "level": 1
                    },
                    "content": [
                        {
                        "type": "text",
                        "text": "Description"
                        }
                    ]
                },                
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""{finding['Description']}"""
                        },
                        {
                            "type": "hardBreak"
                        }
                    ]
                },
                {
                    "type": "heading",
                    "attrs": {
                        "level": 1
                    },
                    "content": [
                        {
                        "type": "text",
                        "text": "Remediation"
                        }
                    ]
                },                
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "text": f"""{finding['Remediation']}""",
                            "type": "text"
                        },
                        {
                            "type": "hardBreak"
                        }
                    ]
                },                
                {
                    "type": "heading",
                    "attrs": {
                        "level": 1
                    },
                    "content": [
                        {
                        "type": "text",
                        "text": "Resources"
                        }
                    ]
                },
                {
                    "type": "codeBlock",
                    "content": [
                        {
                            "text": f"""{finding['Resources']}""",
                            "type": "text"
                        }
                    ]
                }
            ]
        },

        "labels": [ finding['ProductName'] ],
        'issuetype': {'name': 'Bug'}
    }

    logger.info(f"jira_dict: {jira_dict}")
    
    try:
        new_issue = jira_connection.create_issue(fields=jira_dict)
        logger.info(f"Created new Jira issue: {new_issue}")
    except Exception as e:
        logger.error(f"Failed to create Jira issue: {e}")


def setup_jira_connection():
    # Retrieve Jira credentials and server info from environment variables
    jira_basic_auth_email = os.getenv("Jira_basicAuth_email")
    jira_basic_auth_api_token = os.getenv("Jira_basicAuth_apiToken")
    jira_server_url = os.getenv("Jira_serverUrl")

    try:
        # Establish Jira connection
        jira_connection = JIRA(
            basic_auth=(jira_basic_auth_email, jira_basic_auth_api_token),
            server=jira_server_url,
            options={"rest_api_version":"3"}
        )
        return jira_connection
    except Exception as e:
        logger.error(f"Failed to establish Jira connection: {e}")
        raise e


def lambda_handler(event, context):
    # Load environment variables
    region = os.getenv("SECURITY_HUB_REGION", os.getenv("AWS_DEFAULT_REGION"))
    regions = os.getenv("REGIONS", os.getenv("AWS_DEFAULT_REGION")).split(",")
    accounts = os.getenv("ACCOUNTS", os.getenv("AWS_DEFAULT_ACCOUNT")).split(",")
    jira_project_key = os.getenv("Jira_projectKey")

    logger.info(f"SecurityHub region: {region}, Monitored regions: {regions}, Accounts: {accounts}")

    # Setup Jira connection once and reuse
    jira_connection = setup_jira_connection()

    # Setup boto3 client once
    client = boto3.client('securityhub', region_name=region)

    PaginationConfig={'PageSize': 100}
    paginator_max_items = os.getenv("PaginatorMaxItems")
    if paginator_max_items:
        PaginationConfig["MaxItems"] = paginator_max_items
        pass
    else:
        # proper action/logging based on the context
        pass

    # Iterate over the accounts
    for account_id in accounts:
        filters = {
            'AwsAccountId': [{'Value': account_id, 'Comparison': 'EQUALS'}],
            'ProductName': [{'Value': 'Inspector', 'Comparison': 'EQUALS'}],
            'RecordState': [{'Value': 'ACTIVE', 'Comparison': 'EQUALS'}],
            'WorkflowStatus': [{'Value': 'NEW', 'Comparison': 'EQUALS'}],
            'FindingProviderFieldsSeverityLabel': [{'Value': 'CRITICAL', 'Comparison': 'EQUALS'}],
            'VulnerabilitiesFixAvailable': [{'Value': 'YES', 'Comparison': 'EQUALS'}]
        }
            
        # Use paginator to handle multiple pages of findings
        pages = client.get_paginator('get_findings').paginate(
            Filters=filters, PaginationConfig=PaginationConfig
        )

        try:
            for page in pages:
                for finding in page.get('Findings', []):
                    logger.info(f"Processing finding ID: {finding['Id']}")
                    
                    # Notify via Jira
                    findings_notifier(jira_connection, finding, jira_project_key)

                    # Update the finding's workflow status to 'NOTIFIED'
                    response = client.batch_update_findings(
                        FindingIdentifiers=[
                            {
                                "Id": finding['Id'],
                                "ProductArn": finding['ProductArn']
                            }
                        ],
                        Workflow={'Status': 'NOTIFIED'}
                    )

                    # Log processed and unprocessed findings
                    for processed_finding in response.get("ProcessedFindings", []):
                        logger.info(f"Successfully processed finding ID: {processed_finding['Id']}, Product ARN: {processed_finding['ProductArn']}")

                    for unprocessed_finding in response.get("UnprocessedFindings", []):
                        logger.error(f"Failed to process finding ID: {unprocessed_finding['FindingIdentifier']['Id']}, "
                                     f"Product ARN: {unprocessed_finding['FindingIdentifier']['ProductArn']}, "
                                     f"Error: {unprocessed_finding['ErrorCode']} - {unprocessed_finding['ErrorMessage']}")

        except client.exceptions.ClientError as e:
            logger.error(f"ClientError when processing findings for account {account_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
