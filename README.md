# Security Findings Exporter CDK Construct

This project provides an AWS CDK construct, `SecurityFindingsExporterCdkConstruct`, which deploys a Lambda function designed to automatically retrieve, process, and export security findings from AWS Security Hub (or similar security services) to a specified destination, such as an S3 bucket or external API.

## Overview

### Lambda Function Purpose

The Lambda function, written in Python, is responsible for automating the retrieval and processing of security findings. It can be configured to:
- **Fetch security findings** from AWS Security Hub or another security service.
- **Process the findings** to extract relevant data points, such as severity, affected resources, and timestamps.
- **Export the findings** to external systems for storage or further analysis, for example, an S3 bucket, DynamoDB table, or a third-party service.

The function is triggered by specific events, such as the generation of new findings in Security Hub or on a scheduled basis.

### Key Features:
- **Automated Security Data Processing**: Automates the entire lifecycle of security findings management.
- **Pluggable Export Destinations**: Supports exporting to various destinations based on your needs.
- **Serverless and Scalable**: Utilizes AWS Lambda's scalability to handle varying amounts of findings.

## Using the `SecurityFindingsExporterCdkConstruct`

This CDK construct simplifies the deployment of the Lambda function and all related infrastructure. It provisions:
- An IAM role with the appropriate permissions.
- The Lambda function that handles security findings.
- Optionally, it can create supporting infrastructure such as S3 buckets or DynamoDB tables, depending on your configuration.

