import copy
import importlib.util
import json
import time
from pathlib import Path
from typing import Annotated, Any, Literal, TypedDict

import boto3
import botocore
import botocore.exceptions
import typer
from mypy_boto3_cloudformation import CloudFormationClient
from mypy_boto3_s3 import S3Client
from nexify.applications import Nexify
from nexify.cli.application import create_app
from nexify.cli.deploy.constants import BASE_TEMPLATE
from nexify.cli.deploy.package import install_requirements, package_lambda_function
from nexify.cli.deploy.types import NexifyConfig
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn

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
        TextColumn("[bold blue]{task.fields[message]}"),
    ) as progress:
        import_app_task = progress.add_task("[cyan]Importing app...", message="Importing Nexify App")
        app = import_app(app_path)
        progress.update(import_app_task, completed=True)
        progress.remove_task(import_app_task)
        print(":white_check_mark: [green]App imported successfully![/green]")

        analyze_app_test = progress.add_task("[cyan]Analyzing app...", message="Analyzing Nexify App")
        lambda_specs = analyze_app(app)
        progress.update(analyze_app_test, completed=True)
        progress.remove_task(analyze_app_test)
        print(":white_check_mark: [green]App analyzed successfully![/green]")

        load_nexify_config_task = progress.add_task(
            "[cyan]Loading config...", message="Loading Nexify config from nexify.json"
        )
        config = load_nexify_config()
        progress.update(load_nexify_config_task, completed=True)
        progress.remove_task(load_nexify_config_task)
        print(":white_check_mark: [green]Config loaded successfully![/green]")

        install_task = progress.add_task("[cyan]Install requirements...", message="Installing requirements")
        install_requirements("requirements.txt", "./.nexify/requirements", config)
        progress.update(install_task, completed=True)
        progress.remove_task(install_task)
        print(":white_check_mark: [green]Requirements installed successfully![/green]")

        package_task = progress.add_task("[cyan]Packaging...", message="Packaging Lambda functions")
        package_lambda_function(
            source_dir=".",
            requirements_dir="./.nexify/requirements",
            output_zip_path=f"./.nexify/{config['service']}.zip",
        )
        progress.update(package_task, completed=True)
        progress.remove_task(package_task)
        print(":white_check_mark: [green]Lambda functions packaged successfully![/green]")

        create_base_stack_task = progress.add_task(
            "[cyan]Creating basic stack...", message="Creating basic CloudFormation stack"
        )
        session = boto3.Session(profile_name=config["provider"]["profile"])
        stack_name = f"{config['service']}-{config['provider']['stage']}"
        cf_client: CloudFormationClient = session.client("cloudformation", region_name=config["provider"]["region"])
        s3_bucket_name = initial_stack_setup(cf_client, stack_name)
        progress.update(create_base_stack_task, completed=True)
        progress.remove_task(create_base_stack_task)
        print(":white_check_mark: [green]Basic stack created successfully![/green]")

        zip_s3_key = f"{timestamp}/{config['service']}.zip"
        upload_zip_task = progress.add_task("[cyan]Uploading zip...", message="Uploading zip to S3")
        s3_client = session.client("s3", region_name=config["provider"]["region"])
        upload_zip_to_s3(s3_client, s3_bucket_name, f"./.nexify/{config['service']}.zip", zip_s3_key)
        progress.update(upload_zip_task, completed=True)
        progress.remove_task(upload_zip_task)

        create_template_task = progress.add_task(
            "[cyan]Creating template...", message="Creating CloudFormation template"
        )
        template = create_template(
            lambda_specs,
            timestamp=timestamp,
            zip_s3_key=zip_s3_key,
            config=config,
        )
        with open("template.json", "w") as f:
            json.dump(template, f, indent=2)
        progress.update(create_template_task, completed=True)
        progress.remove_task(create_template_task)
        print(":white_check_mark: [green]Template created successfully![/green]")

        stack_update_task = progress.add_task(
            "[cyan]CloudFormation Stack Update...", message="Updating CloudFormation Stack"
        )
        service_endpoint = update_stack(cf_client, stack_name, template)
        progress.update(stack_update_task, completed=True)
        progress.remove_task(stack_update_task)
        print(":white_check_mark: [green]Stack updated successfully![/green]")

    print(":tada: [green]Deployment successful![/green]")

    msg = "Endpoints:\n"
    for spec in lambda_specs:
        url = f"{service_endpoint}{spec['path']}"
        msg += f"\t- [green]{spec['method']:5s}[/green] [link={url}]{url}[/link]\n"
    print(msg)


def import_app(path: Path) -> Nexify:
    app_path = path.resolve()

    if not app_path.exists():
        raise typer.BadParameter(f"File [bright_green]'{app_path}'[/bright_green] does not exist.")

    module_name = app_path.stem
    spec = importlib.util.spec_from_file_location(module_name, app_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from [bright_green]'{app_path}'[/bright_green]")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "app"):
        raise AttributeError(f"No [blue]'app'[/blue] object found in [bright_green]'{app_path}'[/bright_green]")

    return module.app


class LambdaSpec(TypedDict):
    identifier: str
    name: str
    path: str
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]
    handler: str
    runtime: str
    memory_size: int
    timeout: int
    architectures: list[Literal["x86_64", "arm64"]]
    description: str


def analyze_app(app: Nexify) -> list[LambdaSpec]:
    lambda_specs = []

    for route in app.router.routes:
        for method in route.methods:
            lambda_spec: LambdaSpec = {
                "identifier": generate_idendity_lambda_name(route.endpoint.__name__),
                "name": f"{route.endpoint.__name__}",
                "path": route.path,
                "method": method,  # type: ignore
                "handler": f"{route.endpoint.__module__}.{route.endpoint.__name__}",
                "runtime": "python3.10",
                "memory_size": 128,
                "timeout": 30,
                "architectures": ["x86_64"],
                "description": route.endpoint.__doc__ or "",
            }
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
            for o in stack.get("Outputs", [])
            if o.get("OutputKey", "") == "NexifyDeploymentBucketName"
        ][0]

    raise Exception("Stack creation failed.")


def upload_zip_to_s3(s3_client: S3Client, bucket_name: str, zip_path: str, zip_key: str) -> None:
    """
    Upload the zip file to the S3 bucket.
    """
    s3_client.upload_file(zip_path, bucket_name, zip_key)


def create_template(
    lambda_specs: list[LambdaSpec], *, timestamp: int, zip_s3_key: str, config: NexifyConfig
) -> dict[str, Any]:
    t = copy.deepcopy(BASE_TEMPLATE)

    # Define Lambda Log Groups
    for spec in lambda_specs:
        log_group_name = f"{spec['identifier']}LogGroup"
        log_group = {
            "Type": "AWS::Logs::LogGroup",
            "Properties": {
                "LogGroupName": f"/aws/lambda/{spec['name']}",
                "RetentionInDays": 30,
            },
        }
        t["Resources"][log_group_name] = log_group

    # Define Iam Role For Lambda Execution
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
                                        "Fn::Sub": f"arn:${{AWS::Partition}}:logs:${{AWS::Region}}:${{AWS::AccountId}}:log-group:/aws/lambda/{spec['name']}:*"  # noqa: E501
                                    }
                                    for spec in lambda_specs
                                ],
                            },
                        ],
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

    # Define Lambda Functions
    for spec in lambda_specs:
        lambda_name = f"{spec['identifier']}LambdaFunction"
        lambda_function = {
            "Type": "AWS::Lambda::Function",
            "Properties": {
                "Code": {"S3Bucket": {"Ref": "NexifyDeploymentBucket"}, "S3Key": zip_s3_key},
                "Handler": spec["handler"],
                "Runtime": spec["runtime"],
                "FunctionName": spec["name"],
                "MemorySize": spec["memory_size"],
                "Timeout": spec["timeout"],
                "Architectures": spec["architectures"],
                "Description": spec["description"],
                "Environment": {"Variables": {}},
                "Role": {"Fn::GetAtt": ["IamRoleLambdaExecution", "Arn"]},
            },
            "DependsOn": [f"{spec['identifier']}LogGroup"],
        }
        t["Resources"][lambda_name] = lambda_function

    # Define Rest API or HTTP API
    # Load existing Rest API or HTTP APi from config
    # If Type is "AWS::ApiGateway::RestApi" or AWS::ApiGatewayV2::Api
    recources = config.get("resources", {}).get("Resources", {})
    service = config.get("service")
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
            "EndpointConfiguration": {"Types": ["EDGE"]},
            "Policy": "",
            "Properties": {"Name": f"{service}-API", "Description": f"API for {service}"},
        }

    t["Resources"][api_gateway_key] = api_gateway

    # Define Rest API or HTTP API Resources
    # Make Tree for API Resources
    api_resources = {
        "full_path": "",
        "children": {},
    }
    for spec in lambda_specs:
        path = spec["path"]
        path_parts = path.split("/")
        current = api_resources
        for part in path_parts[1:]:
            if part not in current["children"]:
                current["children"][part] = {"full_path": f"{current['full_path']}/{part}", "children": {}}
            current = current["children"][part]

    # Define API Resources from Tree
    def create_api_resource(resource: dict, parent_id: dict | None = None):
        if resource["full_path"] == "":
            for child in resource["children"]:
                create_api_resource(resource["children"][child], {"Fn::GetAtt": [api_gateway_key, "RootResourceId"]})
            return

        resource_id = generate_idendity_api_resource_name(resource["full_path"])
        t["Resources"][resource_id] = {
            "Type": "AWS::ApiGateway::Resource",
            "Properties": {
                "ParentId": parent_id,
                "PathPart": resource["full_path"].split("/")[-1],
                "RestApiId": {"Ref": api_gateway_key},
            },
        }

        for child in resource["children"]:
            create_api_resource(resource["children"][child], {"Ref": resource_id})

    create_api_resource(api_resources)

    # Define API Gateway Permission to invoke Lambda
    for spec in lambda_specs:
        lambda_function_id = f"{spec['identifier']}LambdaFunction"
        permission_id = f"{lambda_function_id}PermissionApiGateway"
        t["Resources"][permission_id] = {
            "Type": "AWS::Lambda::Permission",
            "Properties": {
                "FunctionName": {
                    "Fn::GetAtt": [lambda_function_id, "Arn"],
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
    for spec in lambda_specs:
        method_id = f"{spec['identifier']}{spec['method']}Method"
        lambda_function_id = f"{spec['identifier']}LambdaFunction"
        permission_id = f"{lambda_function_id}PermissionApiGateway"
        t["Resources"][method_id] = {
            "Type": "AWS::ApiGateway::Method",
            "Properties": {
                "HttpMethod": spec["method"],
                "RequestParameters": {},
                "ResourceId": get_idendity_api_resource_id(spec["path"], api_gateway_key),
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
                                {"Fn::GetAtt": ["ReadItemsLambdaFunction", "Arn"]},
                                "/invocations",
                            ],
                        ]
                    },
                },
                "MethodResponses": [],
            },
            "DependsOn": [permission_id],
        }

    # Define API Gateway Deployment
    # TODO: If HTTP API, use AWS::ApiGatewayV2::Deployment
    t["Resources"][f"APIGatewayDeployment{timestamp}"] = {
        "Type": "AWS::ApiGateway::Deployment",
        "Properties": {
            "RestApiId": {"Ref": api_gateway_key},
            "StageName": config["provider"]["stage"],
        },
        "DependsOn": [f"{spec['identifier']}{spec['method']}Method" for spec in lambda_specs],
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


def generate_idendity_lambda_name(lambda_name: str) -> str:
    """
    Generate a Lambda function name based on the endpoint name.
    - First letter is capitalized
    - Underscores are removed and the following letter is capitalized
    - The rest is left as is
    """
    return lambda_name.title().replace("_", "")


def generate_idendity_api_resource_name(resource_path: str) -> str:
    """
    Generate an API Gateway resource name based on the resource path.
    - First letter is capitalized
    - Slashes are removed and the following letter is capitalized
    - The rest is left as is
    - {user_id} -> UserIdVar
    """
    return "ApiGatewayResource" + resource_path.title().replace("/", "").replace("{", "").replace("_", "").replace(
        "}", "Var"
    )


def get_idendity_api_resource_id(resource_path: str, api_gateway_key: str) -> dict[str, list[str] | str]:
    """
    Generate an API Gateway resource name based on the resource path.
    - First letter is capitalized
    - Slashes are removed and the following letter is capitalized
    - The rest is left as is
    - {user_id} -> UserIdVar
    """
    if resource_path == "/":
        return {"Fn::GetAtt": [api_gateway_key, "RootResourceId"]}

    return {"Ref": generate_idendity_api_resource_name(resource_path)}
