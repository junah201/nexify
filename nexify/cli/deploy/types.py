from typing import TypedDict


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
