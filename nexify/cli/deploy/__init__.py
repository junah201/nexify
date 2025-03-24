import copy
import importlib.util
import json
import os
import time
from pathlib import Path
from typing import Annotated, Any

import boto3
import botocore
import botocore.exceptions
import typer
from mypy_boto3_cloudformation import CloudFormationClient
from mypy_boto3_s3 import S3Client
from nexify.applications import Nexify
from nexify.cli.application import create_app
from nexify.cli.deploy.constants import BASE_TEMPLATE
from nexify.cli.deploy.environ import load_env
from nexify.cli.deploy.package import install_requirements, package_lambda_function
from nexify.cli.deploy.types import LambdaSpec, NexifyConfig, RouteLambdaSpec, ScheduleLambdaSpec
from nexify.openapi.docs import get_redoc_html, get_swagger_ui_html
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

app, logger = create_app()


@app.command()
def deploy(
    app_path: Annotated[Path, typer.Argument(help="Path to the main app file")] = Path("./main.py"),
) -> None:
    """
    Deploy your Nexify app to AWS.
    """

    timestamp = int(time.time() * 1000)

    with Progress(
        SpinnerColumn(),
        "{task.description}...",
        TimeElapsedColumn(),
        TextColumn("[bold blue]{task.fields[status]}"),
    ) as progress:
        import_app_task = progress.add_task("Importing Nexify app", status="")
        app = import_app(app_path)
        progress.update(import_app_task, completed=True)
        progress.remove_task(import_app_task)
        print("[green]:heavy_check_mark:[/green] App imported successfully!")

        load_nexify_config_task = progress.add_task("Loading Nexify config from nexify.json", status="")
        config = load_nexify_config()
        progress.update(load_nexify_config_task, completed=True)
        progress.remove_task(load_nexify_config_task)
        print("[green]:heavy_check_mark:[/green] Config loaded successfully!")

        load_env_task = progress.add_task("Loading environment variables", status="")
        load_env(Path.cwd())
        progress.update(load_env_task, completed=True)
        progress.remove_task(load_env_task)
        print("[green]:heavy_check_mark:[/green] Environment variables loaded successfully!")

        analyze_app_test = progress.add_task("Analyzing Nexify app", status="")
        lambda_specs = analyze_app(app, config=config)
        progress.update(analyze_app_test, completed=True)
        progress.remove_task(analyze_app_test)
        print("[green]:heavy_check_mark:[/green] App analyzed successfully!")

        install_task = progress.add_task("Installing requirements", status="")
        install_requirements(
            "requirements.txt", "./.nexify/requirements", config=config, progress=progress, task=install_task
        )
        progress.update(install_task, completed=True)
        progress.remove_task(install_task)
        print("[green]:heavy_check_mark:[/green] Requirements installed successfully!")

        package_task = progress.add_task("Packaging Lambda functions", status="")
        package_lambda_function(
            source_dir=".",
            requirements_dir="./.nexify/requirements",
            output_zip_path=f"./.nexify/{config['service']}.zip",
        )
        progress.update(package_task, completed=True)
        progress.remove_task(package_task)
        print("[green]:heavy_check_mark:[/green] Lambda functions packaged successfully!")

        create_base_stack_task = progress.add_task("Creating basic CloudFormation stack", status="")
        session = boto3.Session(profile_name=config["provider"]["profile"])
        stack_name = f"{config['service']}-{config['provider']['stage']}"
        cf_client: CloudFormationClient = session.client("cloudformation", region_name=config["provider"]["region"])
        s3_bucket_name = initial_stack_setup(cf_client, stack_name)
        progress.update(create_base_stack_task, completed=True)
        progress.remove_task(create_base_stack_task)
        print("[green]:heavy_check_mark:[/green] Basic stack created successfully!")

        zip_s3_key = f"{timestamp}/{config['service']}.zip"
        upload_zip_task = progress.add_task("Uploading zip to S3", status="")
        s3_client = session.client("s3", region_name=config["provider"]["region"])
        upload_zip_to_s3(s3_client, s3_bucket_name, f"./.nexify/{config['service']}.zip", zip_s3_key)
        progress.update(upload_zip_task, completed=True)
        progress.remove_task(upload_zip_task)

        create_template_task = progress.add_task("Creating CloudFormation template", status="")
        template = create_template(
            lambda_specs,
            app=app,
            timestamp=timestamp,
            zip_s3_key=zip_s3_key,
            config=config,
        )

        progress.update(create_template_task, completed=True)
        progress.remove_task(create_template_task)
        print("[green]:heavy_check_mark:[/green] Template created successfully!")

        stack_update_task = progress.add_task("Updating CloudFormation Stack", status="")
        service_endpoint = update_stack(cf_client, stack_name, template)
        progress.update(stack_update_task, completed=True)
        progress.remove_task(stack_update_task)
        print("[green]:heavy_check_mark:[/green] Stack updated successfully!")

    print(":tada: [green]Deployment successful![/green]\n")

    msg = "Endpoints:\n"
    for spec in lambda_specs:
        if not isinstance(spec, RouteLambdaSpec):
            continue
        url = f"{service_endpoint}{spec.path}"
        msg += f"    - [green]{spec.method:5s}[/green] [link={url}]{url}[/link]\n"

    msg += "\n\nAPI Docs:\n"
    for endpoint, name in [("openapi.json", "openapi"), ("docs", "Swagger"), ("redoc", "ReDoc")]:
        url = f"{service_endpoint}/{endpoint}"
        msg += f"    - [green]{name:10s}[/green] [link={url}]{url}[/link]\n"

    msg += "\n\nFunctions:\n"
    for spec in lambda_specs:
        url = f"https://{config['provider']['region']}.console.aws.amazon.com/lambda/home?region={config['provider']['region']}#/functions/{spec.name}?tab=code"
        msg += f"    - [blue][link={url}]{spec.name}[/link][/blue]\n"

    print(msg)


def import_app(path: Path) -> Nexify:
    app_path = path.resolve()

    if not app_path.exists():
        raise typer.BadParameter(f"File '{app_path}' does not exist.")

    module_name = app_path.stem
    spec = importlib.util.spec_from_file_location(module_name, app_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from '{app_path}'")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "app"):
        raise AttributeError(f"No [blue]'app'[/blue] object found in '{app_path}'")

    return module.app


def analyze_app(app: Nexify, *, config: NexifyConfig) -> list[LambdaSpec]:
    lambda_specs = []

    for route in app.router.operations:
        for method in route.methods:
            lambda_spec = RouteLambdaSpec(
                route,
                method=method,
                config=config,
            )
            lambda_specs.append(lambda_spec)

    for schedule in app.scheduler.operations:
        lambda_spec = ScheduleLambdaSpec(schedule, config=config)
        lambda_specs.append(lambda_spec)

    return lambda_specs


def load_nexify_config() -> NexifyConfig:
    dest = Path.cwd() / "nexify.json"

    if not dest.exists():
        raise FileNotFoundError("nexify.json file not found.")

    with open(dest, encoding="utf-8") as f:
        settings = json.load(f)

    return settings


def initial_stack_setup(cf_client: CloudFormationClient, stack_name: str) -> str:
    """
    If the stack does not exist, create the stack with the base template.
    This base template includes the following resources:
    - AWS S3 Bucket for deployment and bucket policy

    Also, it returns the s3 deployment bucket name.
    """
    try:
        response = cf_client.describe_stacks(StackName=stack_name)
        for stack in response["Stacks"]:
            if stack["StackStatus"] == "DELETE_COMPLETE":
                continue
            if stack["StackName"] != stack_name:
                continue

            return [
                o.get("OutputValue", "")
                for o in stack.get("Outputs", [])
                if o.get("OutputKey", "") == "NexifyDeploymentBucketName"
            ][0]
    except botocore.exceptions.ClientError:
        t = copy.deepcopy(BASE_TEMPLATE)

        cf_client.create_stack(StackName=stack_name, TemplateBody=json.dumps(t))
        waiter = cf_client.get_waiter("stack_create_complete")
        waiter.wait(StackName=stack_name)

        response = cf_client.describe_stacks(StackName=stack_name)
        return [
            o.get("OutputValue", "")
            for o in response["Stacks"][0].get("Outputs", [])
            if o.get("OutputKey", "") == "NexifyDeploymentBucketName"
        ][0]

    raise Exception("Stack creation failed.")


def upload_zip_to_s3(s3_client: S3Client, bucket_name: str, zip_path: str, zip_key: str) -> None:
    """
    Upload the zip file to the S3 bucket.
    """
    s3_client.upload_file(zip_path, bucket_name, zip_key)


def create_template(
    lambda_specs: list[LambdaSpec], *, app: Nexify, timestamp: int, zip_s3_key: str, config: NexifyConfig
) -> dict[str, Any]:
    t = copy.deepcopy(BASE_TEMPLATE)

    # Define Lambda Log Groups
    for spec in lambda_specs:
        t["Resources"][spec.log_group_key] = {
            "Type": "AWS::Logs::LogGroup",
            "Properties": {
                "LogGroupName": spec.log_group_name,
                "RetentionInDays": spec.log_retention_in_days,
            },
        }

    # Define Iam Role For Lambda Execution
    iam_role_statement = config["provider"].get("iamRoleStatements", [])

    t["Resources"]["IamRoleLambdaExecution"] = {
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
                        "Fn::Join": [
                            "-",
                            [
                                "nexify",
                                config["service"],
                                config["provider"]["stage"],
                                {"Ref": "AWS::Region"},
                                "lambdaPolicy",
                            ],
                        ]
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
                                        "Fn::Sub": f"arn:${{AWS::Partition}}:logs:${{AWS::Region}}:${{AWS::AccountId}}:log-group:{spec.log_group_name}:*"  # noqa: E501
                                    }
                                    for spec in lambda_specs
                                ],
                            },
                        ]
                        + iam_role_statement,
                    },
                }
            ],
            "Path": "/",
            "RoleName": {
                "Fn::Join": [
                    "-",
                    [
                        "nexify",
                        config["service"],
                        config["provider"]["stage"],
                        {"Ref": "AWS::Region"},
                        "lambdaRole",
                    ],
                ]
            },
        },
    }

    def complie_env():
        env = {}
        for key, value in config["provider"].get("environment", {}).items():
            # 만약 value가 ${env:YOUR_CUSTOM_ENV}와 같은 형식이면, 해당 환경변수를 가져와서 value로 대체
            if value.startswith("${env:") and value.endswith("}"):
                env_key = value[6:-1]
                value = os.environ.get(env_key, "")
            env[key] = value

        return env

    env = complie_env()

    # Define Lambda Functions
    for spec in lambda_specs:
        t["Resources"][spec.lambda_function_key] = {
            "Type": "AWS::Lambda::Function",
            "Properties": {
                "Code": {"S3Bucket": {"Ref": "NexifyDeploymentBucket"}, "S3Key": zip_s3_key},
                "Handler": spec.handler,
                "Runtime": spec.runtime,
                "FunctionName": spec.lambda_function_name,
                "MemorySize": spec.memory_size,
                "Timeout": spec.timeout,
                "Architectures": spec.architectures,
                "Description": spec.description,
                "Environment": {"Variables": env},
                "Role": {"Fn::GetAtt": ["IamRoleLambdaExecution", "Arn"]},
            },
            "DependsOn": [spec.log_group_key],
        }

    # Define Rest API or HTTP API
    # Load existing Rest API or HTTP APi from config
    # If Type is "AWS::ApiGateway::RestApi" or AWS::ApiGatewayV2::Api
    recources = config.get("resources", {}).get("Resources", {})
    service = config.get("service")

    t["Resources"].update(recources)

    api_gateway_key = None
    api_gateway = None
    for key, value in recources.items():
        if value.get("Type") in ["AWS::ApiGateway::RestApi", "AWS::ApiGatewayV2::Api"]:
            api_gateway_key = key
            api_gateway = value
            break
    else:
        # If no existing Rest API or HTTP API found, create a new one
        api_gateway_key = "APIGatewayRestAPI"
        api_gateway = {
            "Type": "AWS::ApiGateway::RestApi",
            "Policy": "",
            "Properties": {
                "Name": f"{service}-API",
                "Description": f"API for {service}",
                "EndpointConfiguration": {"Types": ["EDGE"]},
            },
        }
        t["Resources"][api_gateway_key] = api_gateway

    route_lambda_specs = [spec for spec in lambda_specs if isinstance(spec, RouteLambdaSpec)]
    schedule_lambda_specs = [spec for spec in lambda_specs if isinstance(spec, ScheduleLambdaSpec)]

    # Define Rest API or HTTP API Resources
    # Make Tree for API Resources
    api_resources = {
        "full_path": "",
        "children": {},
        "spec": None,
    }
    for spec in route_lambda_specs:
        path = spec.path
        path_parts = path.split("/")
        current = api_resources
        for part in path_parts[1:]:
            if part not in current["children"]:
                current["children"][part] = {
                    "full_path": f"{current['full_path']}/{part}",
                    "children": {},
                    "resource_key": RouteLambdaSpec.get_api_gateway_resource_key(f"{current['full_path']}/{part}"),
                }
            current = current["children"][part]

    # Define API Resources from Tree
    def create_api_resource(resource: dict, parent_id: dict | None = None):
        if resource["full_path"] == "" or resource["full_path"] == "/":
            for child in resource["children"]:
                create_api_resource(resource["children"][child], {"Fn::GetAtt": [api_gateway_key, "RootResourceId"]})
            return

        t["Resources"][resource["resource_key"]] = {
            "Type": "AWS::ApiGateway::Resource",
            "Properties": {
                "ParentId": parent_id,
                "PathPart": resource["full_path"].split("/")[-1],
                "RestApiId": {"Ref": api_gateway_key},
            },
        }

        for child in resource["children"]:
            create_api_resource(resource["children"][child], {"Ref": resource["resource_key"]})

    create_api_resource(api_resources)

    # Define API Gateway Permission to invoke Lambda
    for spec in route_lambda_specs:
        t["Resources"][spec.permission_key] = {
            "Type": "AWS::Lambda::Permission",
            "Properties": {
                "FunctionName": {
                    "Fn::GetAtt": [spec.lambda_function_key, "Arn"],
                },
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
                            {"Ref": api_gateway_key},
                            "/*/*",
                        ],
                    ]
                },
            },
        }

    # Define API Gateway Method
    for spec in route_lambda_specs:
        t["Resources"][spec.api_gateway_method_key] = {
            "Type": "AWS::ApiGateway::Method",
            "Properties": {
                "HttpMethod": spec.method,
                "RequestParameters": {},
                "ResourceId": spec.get_api_gateway_resource_id(api_gateway_key),
                "RestApiId": {"Ref": api_gateway_key},
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
                                {"Fn::GetAtt": [spec.lambda_function_key, "Arn"]},
                                "/invocations",
                            ],
                        ]
                    },
                },
                "MethodResponses": [],
            },
            "DependsOn": [spec.permission_key],
        }

    # Add method and resource for OpenAPI
    openapi_json = copy.deepcopy(app.openapi())
    os.makedirs("./.nexify", exist_ok=True)
    with open("./.nexify/openapi.json", "w") as f:
        json.dump(openapi_json, f, indent=2)
    openapi_json_string = json.dumps(openapi_json)
    openapi_json_string = openapi_json_string.replace(
        "$ref",
        "\$ref",  # noqa: W605
    )  # It only for resolving this issue: https://github.com/junah201/nexify/issues/6

    openapi_json["servers"] = [
        {
            "url": f"/{config['provider']['stage']}",
        }
    ] + openapi_json.get("servers", [])
    t["Resources"]["NexifyOpenAPIResource"] = {
        "Type": "AWS::ApiGateway::Resource",
        "Properties": {
            "ParentId": {"Fn::GetAtt": [api_gateway_key, "RootResourceId"]},
            "PathPart": "openapi.json",
            "RestApiId": {"Ref": api_gateway_key},
        },
    }
    t["Resources"]["NexifyOpenAPIMethod"] = {
        "Type": "AWS::ApiGateway::Method",
        "Properties": {
            "AuthorizationType": "NONE",
            "HttpMethod": "GET",
            "MethodResponses": [{"StatusCode": "200", "ResponseModels": {}}],
            "RequestParameters": {},
            "Integration": {
                "Type": "MOCK",
                "RequestTemplates": {"application/json": "{statusCode:200}"},
                "IntegrationResponses": [
                    {"StatusCode": "200", "ResponseTemplates": {"application/json": openapi_json_string}}
                ],
            },
            "ResourceId": {"Ref": "NexifyOpenAPIResource"},
            "RestApiId": {"Ref": api_gateway_key},
        },
    }

    swagger_ui_html = get_swagger_ui_html(openapi_url="openapi.json", title=app.title)
    t["Resources"]["NexifySwaggerUIResource"] = {
        "Type": "AWS::ApiGateway::Resource",
        "Properties": {
            "ParentId": {"Fn::GetAtt": [api_gateway_key, "RootResourceId"]},
            "PathPart": "docs",
            "RestApiId": {"Ref": api_gateway_key},
        },
    }
    t["Resources"]["NexifySwaggerUIMethod"] = {
        "Type": "AWS::ApiGateway::Method",
        "Properties": {
            "AuthorizationType": "NONE",
            "HttpMethod": "GET",
            "MethodResponses": [
                {
                    "StatusCode": "200",
                    "ResponseParameters": {
                        "method.response.header.Content-Type": True,
                    },
                }
            ],
            "RequestParameters": {},
            "Integration": {
                "Type": "MOCK",
                "RequestTemplates": {"application/json": "{statusCode:200}"},
                "IntegrationResponses": [
                    {
                        "StatusCode": "200",
                        "ResponseTemplates": {"text/html": swagger_ui_html},
                        "ResponseParameters": {
                            "method.response.header.Content-Type": "'text/html'",
                        },
                    }
                ],
            },
            "ResourceId": {"Ref": "NexifySwaggerUIResource"},
            "RestApiId": {"Ref": api_gateway_key},
        },
    }

    redoc_html = get_redoc_html(openapi_url="openapi.json", title=app.title)
    t["Resources"]["NexifyReDocResource"] = {
        "Type": "AWS::ApiGateway::Resource",
        "Properties": {
            "ParentId": {"Fn::GetAtt": [api_gateway_key, "RootResourceId"]},
            "PathPart": "redoc",
            "RestApiId": {"Ref": api_gateway_key},
        },
    }
    t["Resources"]["NexifyReDocMethod"] = {
        "Type": "AWS::ApiGateway::Method",
        "Properties": {
            "AuthorizationType": "NONE",
            "HttpMethod": "GET",
            "MethodResponses": [
                {
                    "StatusCode": "200",
                    "ResponseParameters": {
                        "method.response.header.Content-Type": True,
                    },
                }
            ],
            "RequestParameters": {},
            "Integration": {
                "Type": "MOCK",
                "RequestTemplates": {"application/json": "{statusCode:200}"},
                "IntegrationResponses": [
                    {
                        "StatusCode": "200",
                        "ResponseTemplates": {"text/html": redoc_html},
                        "ResponseParameters": {
                            "method.response.header.Content-Type": "'text/html'",
                        },
                    }
                ],
            },
            "ResourceId": {"Ref": "NexifyReDocResource"},
            "RestApiId": {"Ref": api_gateway_key},
        },
    }

    # Define API Gateway Deployment
    # TODO: If HTTP API, use AWS::ApiGatewayV2::Deployment
    t["Resources"][f"APIGatewayDeployment{timestamp}"] = {
        "Type": "AWS::ApiGateway::Deployment",
        "Properties": {
            "RestApiId": {"Ref": api_gateway_key},
            "StageName": config["provider"]["stage"],
        },
        "DependsOn": [spec.api_gateway_method_key for spec in route_lambda_specs],
    }

    # Define Scheduled Events
    for spec in schedule_lambda_specs:
        for expression in spec.expressions:
            t["Resources"][f"{spec.identifier}{expression.rule_key}"] = {
                "Type": "AWS::Events::Rule",
                "Properties": {
                    "Description": spec.description,
                    "Name": f"{spec.identifier}{expression.rule_name}",
                    "ScheduleExpression": str(expression),
                    "State": "ENABLED",
                    "Targets": [
                        {
                            "Arn": {"Fn::GetAtt": [spec.lambda_function_key, "Arn"]},
                            "Id": spec.name,
                        }
                    ],
                },
            }

    # Define Permissions for Scheduled Events
    for spec in schedule_lambda_specs:
        for expression in spec.expressions:
            t["Resources"][f"{spec.identifier}{expression.permission_key}"] = {
                "Type": "AWS::Lambda::Permission",
                "Properties": {
                    "Action": "lambda:InvokeFunction",
                    "FunctionName": {"Fn::GetAtt": [spec.lambda_function_key, "Arn"]},
                    "Principal": "events.amazonaws.com",
                    "SourceArn": {
                        "Fn::Join": [
                            "",
                            [
                                "arn:",
                                {"Ref": "AWS::Partition"},
                                ":events:",
                                {"Ref": "AWS::Region"},
                                ":",
                                {"Ref": "AWS::AccountId"},
                                ":rule/",
                                f"{spec.identifier}{expression.rule_key}",
                            ],
                        ]
                    },
                },
            }

    # Add Outputs
    t["Outputs"]["ServiceEndpoint"] = {
        "Description": "URL of the service endpoint",
        "Value": {
            "Fn::Join": [
                "",
                [
                    "https://",
                    {"Ref": api_gateway_key},
                    ".execute-api.",
                    {"Ref": "AWS::Region"},
                    ".",
                    {"Ref": "AWS::URLSuffix"},
                    "/",
                    config["provider"]["stage"],
                ],
            ]
        },
        "Export": {"Name": f"nexify-{config['service']}-{config['provider']['stage']}-ServiceEndpoint"},
    }

    os.makedirs("./.nexify", exist_ok=True)
    with open("./.nexify/template.json", "w") as f:
        json.dump(t, f, indent=2)

    return t


def update_stack(cf_client: CloudFormationClient, stack_name: str, template: dict[str, Any]) -> str:
    cf_client.update_stack(
        StackName=stack_name, TemplateBody=json.dumps(template), Capabilities=["CAPABILITY_NAMED_IAM"]
    )

    waiter = cf_client.get_waiter("stack_update_complete")
    waiter.wait(StackName=stack_name)

    response = cf_client.describe_stacks(StackName=stack_name)
    for stack in response["Stacks"]:
        if stack["StackStatus"] == "DELETE_COMPLETE":
            continue
        if stack["StackName"] != stack_name:
            continue

        return [
            o.get("OutputValue", "") for o in stack.get("Outputs", []) if o.get("OutputKey", "") == "ServiceEndpoint"
        ][0]

    raise Exception("Stack update failed.")
