BASE_TEMPLATE = {
    "AWSTemplateFormatVersion": "2010-09-09",
    "Description": "The AWS CloudFormation template for this Nexify application",
    "Resources": {
        "NexifyDeploymentBucket": {
            "Type": "AWS::S3::Bucket",
            "Properties": {
                "BucketEncryption": {
                    "ServerSideEncryptionConfiguration": [{"ServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
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
    },
    "Outputs": {"NexifyDeploymentBucketName": {"Value": {"Ref": "NexifyDeploymentBucket"}}},
}
