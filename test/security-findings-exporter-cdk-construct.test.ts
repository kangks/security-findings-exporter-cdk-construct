import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';
import { SecurityFindingsExporterCdkConstruct } from '../lib/index';

test('Lambda Function and Roles are created', () => {
  // GIVEN
  const app = new cdk.App();
  const stack = new cdk.Stack(app, 'TestStack');

  // WHEN
  new SecurityFindingsExporterCdkConstruct(stack, 'SecurityFindingsExporter', {
    securityFindingsRegions: "",
    securityFindingsAccounts: "",
    jiraBasicAuthEmail: "",
    jiraBasicAuthApiToken: "",
    jiraServerUrl: "",
    jiraProjectKey: ""
  
  });

  // THEN
  const template = Template.fromStack(stack);

  console.log(template)

  // Assert that a Lambda function is created
  template.hasResourceProperties('AWS::Lambda::Function', {
    Runtime: 'python3.12', // Adjust this based on your actual runtime
    Handler: 'index.lambda_handler'
  });

  // Assert that an IAM role is created for the Lambda function
  template.hasResourceProperties('AWS::IAM::Role', {
    AssumeRolePolicyDocument: {
      Statement: Match.arrayWith([
        Match.objectLike({
          Effect: 'Allow',
          Principal: {
            Service: 'lambda.amazonaws.com',
          },
          Action: 'sts:AssumeRole',
        }),
      ]),
    },
  });
});
