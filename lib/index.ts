import * as cdk from 'aws-cdk-lib';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { Construct } from 'constructs';
import * as path from 'path';

export interface SecurityFindingsExporterCdkConstructProps extends cdk.StackProps{
  readonly securityFindingsRegions: string,
  readonly securityFindingsAccounts: string,
  readonly jiraBasicAuthEmail: string,
  readonly jiraBasicAuthApiToken: string,
  readonly jiraServerUrl: string,
  readonly jiraProjectKey: string
}

export class SecurityFindingsExporterCdkConstruct extends Construct {

  public readonly functionARN:string;

  constructor(scope: Construct, id: string, props: SecurityFindingsExporterCdkConstructProps) {
    super(scope, id);

    const aggregatedLogGroup = new cdk.aws_logs.LogGroup(this, 'SecurityFindingsNotifierLogGroup', {
      logGroupName: '/aws/lambda/SecurityFindingsNotifier',
    });

    var lambdaFunction = new PythonFunction(this, "SecurityFindingsNotifier", {
      entry: path.join(__dirname, '..', 'functions', 'security-findings-exporter'),
      runtime: cdk.aws_lambda.Runtime.PYTHON_3_12,
      architecture: cdk.aws_lambda.Architecture.ARM_64,
      handler:"lambda_handler",
      timeout: cdk.Duration.seconds(200),
      logGroup: aggregatedLogGroup,
      environment: {
        LOG_LEVEL: 'INFO',
        REGIONS: props.securityFindingsRegions,
        ACCOUNTS: props.securityFindingsAccounts,
        Jira_basicAuth_email: props.jiraBasicAuthEmail,
        Jira_basicAuth_apiToken: props.jiraBasicAuthApiToken,
        Jira_serverUrl: props.jiraServerUrl,
        Jira_projectKey: props.jiraProjectKey
      },              
    });

    lambdaFunction.addToRolePolicy(
      new cdk.aws_iam.PolicyStatement({
        actions: [
          "securityhub:GetFindings",
          "securityhub:BatchUpdateFindings"
        ],
        resources: ['*'],
      })
    );

    this.functionARN = lambdaFunction.functionArn;    
  }
}
