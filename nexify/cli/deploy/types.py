from typing import Annotated, Literal, TypedDict

from nexify.operation import Operation
from nexify.routing import Route
from nexify.schedule import Schedule
from typing_extensions import Doc


class IAMRoleStatement(TypedDict):
    Effect: str
    Action: list[str]
    Resource: str


class Provider(TypedDict):
    name: str
    runtime: str
    region: str
    profile: str
    logRetentionInDays: int
    architecture: str
    memorySize: int
    timeout: int
    stage: str
    environment: dict[str, str]
    iamRoleStatements: list[IAMRoleStatement]


class Package(TypedDict):
    include: list[str]
    exclude: list[str]


class APIGatewayRestAPIProperties(TypedDict):
    Name: str
    Description: str


class APIGatewayRestAPI(TypedDict):
    Type: str
    Properties: APIGatewayRestAPIProperties


class Resources(TypedDict):
    Resources: dict[str, APIGatewayRestAPI]


class NexifyConfig(TypedDict):
    service: str
    provider: Provider
    package: Package
    resources: Resources


class LambdaSpec:
    def __init__(
        self,
        operation: Operation,
        config: NexifyConfig,
    ):
        self.name = operation.handler.__name__
        self.identifier = self.name.title().replace("_", "")
        self.handler = f"{operation.handler.__module__}.{operation.handler.__name__}"
        self.description = operation.handler.__doc__ or ""
        self.runtime = getattr(operation, "runtime", None) or config["provider"].get("runtime", "python3.10")
        self.memory_size = getattr(operation, "memory_size", None) or config["provider"].get("memorySize", 128)
        self.timeout = getattr(operation, "timeout", None) or config["provider"].get("timeout", 3)
        self.architectures = getattr(operation, "architectures", None) or [
            config["provider"].get("architecture", "x86_64")
        ]
        self.log_retention_in_days = getattr(operation, "log_retention_in_days", None) or config["provider"].get(
            "logRetentionInDays", 30
        )

    @property
    def log_group_key(self) -> str:
        """
        Log group key for the CloudFormation template.
        """
        return f"{self.identifier}LogGroup"

    @property
    def log_group_name(self) -> str:
        """
        Actual log group name.
        e.g. /aws/lambda/MyLambdaFunction
        """
        return f"/aws/lambda/{self.name}"

    @property
    def lambda_function_key(self) -> str:
        """
        Lambda function key for the CloudFormation template.
        """
        return f"{self.identifier}LambdaFunction"

    @property
    def lambda_function_name(self) -> str:
        """
        Actual Lambda function name.
        """
        return self.name


class RouteLambdaSpec(LambdaSpec):
    def __init__(
        self,
        route: Route,
        method: Annotated[
            Literal["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
            Doc("The HTTP method."),
        ],
        config: NexifyConfig,
    ):
        super().__init__(route, config=config)
        self.path = route.path
        self.method = method

    @property
    def permission_key(self) -> str:
        """
        Permission key for the CloudFormation template.
        This permission allows API Gateway to invoke the Lambda function.
        """
        return f"{self.lambda_function_key}PermissionApiGateway"

    @property
    def api_gateway_method_key(self) -> str:
        """
        Method key for the CloudFormation template.
        This is the method that will be attached to the API Gateway.
        """
        return f"{self.identifier}{self.method}Method"

    @property
    def api_gateway_resource_key(self) -> str:
        """
        Resource key for the CloudFormation template.
        This is the resource that will be attached to the API Gateway.
        - First letter is capitalized
        - Slashes are removed and the following letter is capitalized
        - The rest is left as is
        - {user_id} -> UserIdVar
        """
        return self.get_api_gateway_resource_key(self.path)

    @classmethod
    def get_api_gateway_resource_key(cls, path: str) -> str:
        """
        Resource key for the CloudFormation template.
        This is the resource that will be attached to the API Gateway.
        - First letter is capitalized
        - Slashes are removed and the following letter is capitalized
        - The rest is left as is
        - {user_id} -> UserIdVar
        """
        return "ApiGatewayResource" + path.title().replace("/", "").replace("{", "").replace("_", "").replace(
            "}", "Var"
        )

    def get_api_gateway_resource_id(self, api_gateway_key: str) -> dict[str, list[str] | str]:
        """
        Resource id for the CloudFormation template.
        This is the resource that will be attached to the API Gateway.
        """
        if self.path == "/":
            return {"Fn::GetAtt": [api_gateway_key, "RootResourceId"]}

        return {"Ref": self.api_gateway_resource_key}


class ScheduleLambdaSpec(LambdaSpec):
    def __init__(
        self,
        schedule: Schedule,
        config: NexifyConfig,
    ):
        super().__init__(schedule, config=config)
        self.expressions = schedule.expressions
