EE_DEPLOYER_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "apigateway:DELETE",
                "apigateway:GET",
                "apigateway:PATCH",
                "apigateway:POST",
                "apigateway:PUT",
                "cloudformation:CreateChangeSet",
                "cloudformation:DescribeChangeSet",
                "cloudformation:DescribeStackEvents",
                "cloudformation:DescribeStacks",
                "cloudformation:ExecuteChangeSet",
                "cloudformation:GetTemplateSummary",
                "events:*",
                "logs:CreateLogGroup",
                "logs:PutRetentionPolicy",
                "s3:AbortMultipartUpload",
                "s3:GetObject",
                "s3:ListBucketMultipartUploads",
                "s3:ListMultipartUploadParts",
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:PutObjectTagging",
            ],
            "Resource": [
                "arn:aws:cloudformation:eu-west-2:*:stack/EEApp*/*",
                "arn:aws:events:eu-west-2:*:rule/*",
            ],
        }
    ],
}

EE_CODE_DEPLOY_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "autoscaling:*",
                "codedeploy:*",
                "ec2:*",
                "elasticloadbalancing:*",
                "iam:AddRoleToInstanceProfile",
                "iam:AttachRolePolicy",
                "iam:CreateInstanceProfile",
                "iam:CreateRole",
                "iam:DeleteInstanceProfile",
                "iam:DeleteRole",
                "iam:DeleteRolePolicy",
                "iam:GetInstanceProfile",
                "iam:GetRole",
                "iam:GetRolePolicy",
                "iam:ListInstanceProfilesForRole",
                "iam:ListRolePolicies",
                "iam:ListRoles",
                "iam:PassRole",
                "iam:PutRolePolicy",
                "iam:RemoveRoleFromInstanceProfile",
                "s3:*",
                "ssm:*",
            ],
            "Resource": "*",
        },
        {
            "Effect": "Allow",
            "Action": "iam:CreateServiceLinkedRole",
            "Resource": "arn:aws:iam::*:role/aws-service-role/elasticloadbalancing.amazonaws.com/AWSServiceRoleForElasticLoadBalancing*",
            "Condition": {
                "StringLike": {
                    "iam:AWSServiceName": "elasticloadbalancing.amazonaws.com"
                }
            },
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:AttachRolePolicy",
                "iam:PutRolePolicy",
                "iam:CreateServiceLinkedRole",
            ],
            "Resource": [
                "arn:aws:iam::*:role/aws-service-role/elasticloadbalancing.amazonaws.com/AWSServiceRoleForElasticLoadBalancing*",
                "arn:aws:iam::*:role/aws-service-role/autoscaling.amazonaws.com/AWSServiceRoleForAutoScaling*",
            ],
        },
    ],
}

EE_CODE_DEPLOY_EC2_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": ["s3:Get*", "s3:List*"],
            "Effect": "Allow",
            "Resource": "arn:aws:s3:::aws-codedeploy-eu-west-2/*",
        },
        {
            "Action": ["s3:*"],
            "Effect": "Allow",
            "Resource": [
                "arn:aws:s3:::dc-ee-production-database-backups/*",
                "arn:aws:s3:::dc-ee-production-database-backups",
            ],
        },
        {
            "Action": [
                "events:DescribeEventBus",
                "events:PutEvents",
                "events:ListEventBuses",
            ],
            "Effect": "Allow",
            "Resource": [
                "arn:aws:events:eu-west-2:*:event-bus/default",
            ],
        },
    ],
}

EE_CODE_DEPLOY_LAUNCH_TEMPLATE_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:RunInstances",
                "ec2:CreateTags",
                "iam:PassRole",
            ],
            "Resource": "*",
        }
    ],
}
