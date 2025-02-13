import time

from nexify.cli.deploy import analyze_app, create_template

mock_settings = {
    "service": "newapp",
    "provider": {
        "name": "aws",
        "runtime": "python3.10",
        "region": "ap-northeast-2",
        "profile": "nexifytest",
        "logRetentionInDays": 14,
        "architecture": "x86_64",
        "memorySize": 128,
        "timeout": 10,
        "stage": "prod",
        "environment": {"YOUR_CUSTOM_ENV": "${env:YOUR_CUSTOM_ENV}"},
        "iamRoleStatements": [{"Effect": "Allow", "Action": ["s3:*"], "Resource": "*"}],
    },
    "package": {"include": ["main.py"], "exclude": [".venv/**", ".git/**", ".gitignore"], "pipCmdExtraArgs": [""]},
    "resources": {
        "Resources": {
            "APIGatewayRestAPI": {
                "Type": "AWS::ApiGateway::RestApi",
                "Properties": {
                    "Name": "newapp-API",
                    "EndpointConfiguration": {"Types": ["EDGE"]},
                    "Policy": "",
                    "Description": "API for newapp",
                },
            }
        }
    },
}


def test_deploy_create_template(basic_app):
    timestamp = int(time.time() * 1000)
    zip_s3_key = f"{timestamp}/{mock_settings['service']}.zip"
    lambda_specs = analyze_app(basic_app, config=mock_settings)
    template = create_template(
        app=basic_app,
        lambda_specs=lambda_specs,
        timestamp=timestamp,
        zip_s3_key=zip_s3_key,
        config=mock_settings,
    )

    del template["Resources"]["NexifyOpenAPIMethod"]
    del template["Resources"]["NexifySwaggerUIMethod"]
    del template["Resources"]["NexifyReDocMethod"]

    assert template == {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "The AWS CloudFormation template for this Nexify application",
        "Resources": {
            "NexifyDeploymentBucket": {
                "Type": "AWS::S3::Bucket",
                "Properties": {
                    "BucketEncryption": {
                        "ServerSideEncryptionConfiguration": [
                            {"ServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}
                        ]
                    }
                },
            },
            "NexifyDeploymentBucketPolicy": {
                "Type": "AWS::S3::BucketPolicy",
                "Properties": {
                    "Bucket": {"Ref": "NexifyDeploymentBucket"},
                    "PolicyDocument": {
                        "Statement": [
                            {
                                "Action": "s3:*",
                                "Effect": "Deny",
                                "Principal": "*",
                                "Resource": [
                                    {
                                        "Fn::Join": [
                                            "",
                                            [
                                                "arn:",
                                                {"Ref": "AWS::Partition"},
                                                ":s3:::",
                                                {"Ref": "NexifyDeploymentBucket"},
                                                "/*",
                                            ],
                                        ]
                                    },
                                    {
                                        "Fn::Join": [
                                            "",
                                            [
                                                "arn:",
                                                {"Ref": "AWS::Partition"},
                                                ":s3:::",
                                                {"Ref": "NexifyDeploymentBucket"},
                                            ],
                                        ]
                                    },
                                ],
                                "Condition": {"Bool": {"aws:SecureTransport": False}},
                            }
                        ]
                    },
                },
            },
            "ReadItemsLogGroup": {
                "Type": "AWS::Logs::LogGroup",
                "Properties": {"LogGroupName": "/aws/lambda/read_items", "RetentionInDays": 14},
            },
            "CreateItemLogGroup": {
                "Type": "AWS::Logs::LogGroup",
                "Properties": {"LogGroupName": "/aws/lambda/create_item", "RetentionInDays": 14},
            },
            "ReadItemLogGroup": {
                "Type": "AWS::Logs::LogGroup",
                "Properties": {"LogGroupName": "/aws/lambda/read_item", "RetentionInDays": 14},
            },
            "IamRoleLambdaExecution": {
                "Type": "AWS::IAM::Role",
                "Properties": {
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"Service": ["lambda.amazonaws.com"]},
                                "Action": ["sts:AssumeRole"],
                            }
                        ],
                    },
                    "Policies": [
                        {
                            "PolicyName": {
                                "Fn::Join": ["-", ["nexify", "newapp", "prod", {"Ref": "AWS::Region"}, "lambdaPolicy"]]
                            },
                            "PolicyDocument": {
                                "Version": "2012-10-17",
                                "Statement": [
                                    {
                                        "Effect": "Allow",
                                        "Action": [
                                            "logs:CreateLogStream",
                                            "logs:CreateLogGroup",
                                            "logs:TagResource",
                                            "logs:PutLogEvents",
                                        ],
                                        "Resource": [
                                            {
                                                "Fn::Sub": "arn:${AWS::Partition}:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/lambda/read_items:*"
                                            },
                                            {
                                                "Fn::Sub": "arn:${AWS::Partition}:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/lambda/create_item:*"
                                            },
                                            {
                                                "Fn::Sub": "arn:${AWS::Partition}:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/lambda/read_item:*"
                                            },
                                        ],
                                    },
                                    {
                                        "Action": [
                                            "s3:*",
                                        ],
                                        "Effect": "Allow",
                                        "Resource": "*",
                                    },
                                ],
                            },
                        }
                    ],
                    "Path": "/",
                    "RoleName": {"Fn::Join": ["-", ["nexify", "newapp", "prod", {"Ref": "AWS::Region"}, "lambdaRole"]]},
                },
            },
            "ReadItemsLambdaFunction": {
                "Type": "AWS::Lambda::Function",
                "Properties": {
                    "Code": {"S3Bucket": {"Ref": "NexifyDeploymentBucket"}, "S3Key": zip_s3_key},
                    "Handler": "nexify.templates.basic.main.read_items",
                    "Runtime": "python3.10",
                    "FunctionName": "read_items",
                    "MemorySize": 128,
                    "Timeout": 10,
                    "Architectures": ["x86_64"],
                    "Description": "",
                    "Environment": {"Variables": {"YOUR_CUSTOM_ENV": ""}},
                    "Role": {"Fn::GetAtt": ["IamRoleLambdaExecution", "Arn"]},
                },
                "DependsOn": ["ReadItemsLogGroup"],
            },
            "CreateItemLambdaFunction": {
                "Type": "AWS::Lambda::Function",
                "Properties": {
                    "Code": {"S3Bucket": {"Ref": "NexifyDeploymentBucket"}, "S3Key": zip_s3_key},
                    "Handler": "nexify.templates.basic.main.create_item",
                    "Runtime": "python3.10",
                    "FunctionName": "create_item",
                    "MemorySize": 128,
                    "Timeout": 10,
                    "Architectures": ["x86_64"],
                    "Description": "",
                    "Environment": {"Variables": {"YOUR_CUSTOM_ENV": ""}},
                    "Role": {"Fn::GetAtt": ["IamRoleLambdaExecution", "Arn"]},
                },
                "DependsOn": ["CreateItemLogGroup"],
            },
            "ReadItemLambdaFunction": {
                "Type": "AWS::Lambda::Function",
                "Properties": {
                    "Code": {"S3Bucket": {"Ref": "NexifyDeploymentBucket"}, "S3Key": zip_s3_key},
                    "Handler": "nexify.templates.basic.main.read_item",
                    "Runtime": "python3.10",
                    "FunctionName": "read_item",
                    "MemorySize": 128,
                    "Timeout": 10,
                    "Architectures": ["x86_64"],
                    "Description": "",
                    "Environment": {"Variables": {"YOUR_CUSTOM_ENV": ""}},
                    "Role": {"Fn::GetAtt": ["IamRoleLambdaExecution", "Arn"]},
                },
                "DependsOn": ["ReadItemLogGroup"],
            },
            "APIGatewayRestAPI": {
                "Type": "AWS::ApiGateway::RestApi",
                "Properties": {
                    "Name": "newapp-API",
                    "EndpointConfiguration": {"Types": ["EDGE"]},
                    "Policy": "",
                    "Description": "API for newapp",
                },
            },
            "ApiGatewayResourceItems": {
                "Type": "AWS::ApiGateway::Resource",
                "Properties": {
                    "ParentId": {"Fn::GetAtt": ["APIGatewayRestAPI", "RootResourceId"]},
                    "PathPart": "items",
                    "RestApiId": {"Ref": "APIGatewayRestAPI"},
                },
            },
            "ApiGatewayResourceItemsItemIdVar": {
                "Type": "AWS::ApiGateway::Resource",
                "Properties": {
                    "ParentId": {"Ref": "ApiGatewayResourceItems"},
                    "PathPart": "{item_id}",
                    "RestApiId": {"Ref": "APIGatewayRestAPI"},
                },
            },
            "ReadItemsLambdaFunctionPermissionApiGateway": {
                "Type": "AWS::Lambda::Permission",
                "Properties": {
                    "FunctionName": {"Fn::GetAtt": ["ReadItemsLambdaFunction", "Arn"]},
                    "Action": "lambda:InvokeFunction",
                    "Principal": "apigateway.amazonaws.com",
                    "SourceArn": {
                        "Fn::Join": [
                            "",
                            [
                                "arn:",
                                {"Ref": "AWS::Partition"},
                                ":execute-api:",
                                {"Ref": "AWS::Region"},
                                ":",
                                {"Ref": "AWS::AccountId"},
                                ":",
                                {"Ref": "APIGatewayRestAPI"},
                                "/*/*",
                            ],
                        ]
                    },
                },
            },
            "CreateItemLambdaFunctionPermissionApiGateway": {
                "Type": "AWS::Lambda::Permission",
                "Properties": {
                    "FunctionName": {"Fn::GetAtt": ["CreateItemLambdaFunction", "Arn"]},
                    "Action": "lambda:InvokeFunction",
                    "Principal": "apigateway.amazonaws.com",
                    "SourceArn": {
                        "Fn::Join": [
                            "",
                            [
                                "arn:",
                                {"Ref": "AWS::Partition"},
                                ":execute-api:",
                                {"Ref": "AWS::Region"},
                                ":",
                                {"Ref": "AWS::AccountId"},
                                ":",
                                {"Ref": "APIGatewayRestAPI"},
                                "/*/*",
                            ],
                        ]
                    },
                },
            },
            "ReadItemLambdaFunctionPermissionApiGateway": {
                "Type": "AWS::Lambda::Permission",
                "Properties": {
                    "FunctionName": {"Fn::GetAtt": ["ReadItemLambdaFunction", "Arn"]},
                    "Action": "lambda:InvokeFunction",
                    "Principal": "apigateway.amazonaws.com",
                    "SourceArn": {
                        "Fn::Join": [
                            "",
                            [
                                "arn:",
                                {"Ref": "AWS::Partition"},
                                ":execute-api:",
                                {"Ref": "AWS::Region"},
                                ":",
                                {"Ref": "AWS::AccountId"},
                                ":",
                                {"Ref": "APIGatewayRestAPI"},
                                "/*/*",
                            ],
                        ]
                    },
                },
            },
            "ReadItemsGETMethod": {
                "Type": "AWS::ApiGateway::Method",
                "Properties": {
                    "HttpMethod": "GET",
                    "RequestParameters": {},
                    "ResourceId": {"Ref": "ApiGatewayResourceItems"},
                    "RestApiId": {"Ref": "APIGatewayRestAPI"},
                    "ApiKeyRequired": False,
                    "AuthorizationType": "NONE",
                    "Integration": {
                        "IntegrationHttpMethod": "POST",
                        "Type": "AWS_PROXY",
                        "Uri": {
                            "Fn::Join": [
                                "",
                                [
                                    "arn:",
                                    {"Ref": "AWS::Partition"},
                                    ":apigateway:",
                                    {"Ref": "AWS::Region"},
                                    ":lambda:path/2015-03-31/functions/",
                                    {"Fn::GetAtt": ["ReadItemsLambdaFunction", "Arn"]},
                                    "/invocations",
                                ],
                            ]
                        },
                    },
                    "MethodResponses": [],
                },
                "DependsOn": ["ReadItemsLambdaFunctionPermissionApiGateway"],
            },
            "CreateItemPOSTMethod": {
                "Type": "AWS::ApiGateway::Method",
                "Properties": {
                    "HttpMethod": "POST",
                    "RequestParameters": {},
                    "ResourceId": {"Ref": "ApiGatewayResourceItems"},
                    "RestApiId": {"Ref": "APIGatewayRestAPI"},
                    "ApiKeyRequired": False,
                    "AuthorizationType": "NONE",
                    "Integration": {
                        "IntegrationHttpMethod": "POST",
                        "Type": "AWS_PROXY",
                        "Uri": {
                            "Fn::Join": [
                                "",
                                [
                                    "arn:",
                                    {"Ref": "AWS::Partition"},
                                    ":apigateway:",
                                    {"Ref": "AWS::Region"},
                                    ":lambda:path/2015-03-31/functions/",
                                    {"Fn::GetAtt": ["CreateItemLambdaFunction", "Arn"]},
                                    "/invocations",
                                ],
                            ]
                        },
                    },
                    "MethodResponses": [],
                },
                "DependsOn": ["CreateItemLambdaFunctionPermissionApiGateway"],
            },
            "ReadItemGETMethod": {
                "Type": "AWS::ApiGateway::Method",
                "Properties": {
                    "HttpMethod": "GET",
                    "RequestParameters": {},
                    "ResourceId": {"Ref": "ApiGatewayResourceItemsItemIdVar"},
                    "RestApiId": {"Ref": "APIGatewayRestAPI"},
                    "ApiKeyRequired": False,
                    "AuthorizationType": "NONE",
                    "Integration": {
                        "IntegrationHttpMethod": "POST",
                        "Type": "AWS_PROXY",
                        "Uri": {
                            "Fn::Join": [
                                "",
                                [
                                    "arn:",
                                    {"Ref": "AWS::Partition"},
                                    ":apigateway:",
                                    {"Ref": "AWS::Region"},
                                    ":lambda:path/2015-03-31/functions/",
                                    {"Fn::GetAtt": ["ReadItemLambdaFunction", "Arn"]},
                                    "/invocations",
                                ],
                            ]
                        },
                    },
                    "MethodResponses": [],
                },
                "DependsOn": ["ReadItemLambdaFunctionPermissionApiGateway"],
            },
            "NexifyOpenAPIResource": {
                "Type": "AWS::ApiGateway::Resource",
                "Properties": {
                    "ParentId": {"Fn::GetAtt": ["APIGatewayRestAPI", "RootResourceId"]},
                    "PathPart": "openapi.json",
                    "RestApiId": {"Ref": "APIGatewayRestAPI"},
                },
            },
            "NexifySwaggerUIResource": {
                "Type": "AWS::ApiGateway::Resource",
                "Properties": {
                    "ParentId": {"Fn::GetAtt": ["APIGatewayRestAPI", "RootResourceId"]},
                    "PathPart": "docs",
                    "RestApiId": {"Ref": "APIGatewayRestAPI"},
                },
            },
            "NexifyReDocResource": {
                "Type": "AWS::ApiGateway::Resource",
                "Properties": {
                    "ParentId": {"Fn::GetAtt": ["APIGatewayRestAPI", "RootResourceId"]},
                    "PathPart": "redoc",
                    "RestApiId": {"Ref": "APIGatewayRestAPI"},
                },
            },
            f"APIGatewayDeployment{timestamp}": {
                "Type": "AWS::ApiGateway::Deployment",
                "Properties": {"RestApiId": {"Ref": "APIGatewayRestAPI"}, "StageName": "prod"},
                "DependsOn": ["ReadItemsGETMethod", "CreateItemPOSTMethod", "ReadItemGETMethod"],
            },
        },
        "Outputs": {
            "NexifyDeploymentBucketName": {"Value": {"Ref": "NexifyDeploymentBucket"}},
            "ServiceEndpoint": {
                "Description": "URL of the service endpoint",
                "Value": {
                    "Fn::Join": [
                        "",
                        [
                            "https://",
                            {"Ref": "APIGatewayRestAPI"},
                            ".execute-api.",
                            {"Ref": "AWS::Region"},
                            ".",
                            {"Ref": "AWS::URLSuffix"},
                            "/",
                            "prod",
                        ],
                    ]
                },
                "Export": {"Name": "nexify-newapp-prod-ServiceEndpoint"},
            },
        },
    }
