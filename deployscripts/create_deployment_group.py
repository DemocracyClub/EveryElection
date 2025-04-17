import os
import time

import boto3
from botocore.exceptions import ClientError

session = boto3.Session()

# hardcoded to name in cdk/code_deploy.py
TARGET_GROUP_NAME = "ee-alb-tg"


def check_deployment_group():
    """
    Attempt to get default deployment group.
    TODO allow this to accept args
    """
    client = session.client(
        "codedeploy", region_name=os.environ.get("AWS_REGION")
    )
    deployment_group = client.get_deployment_group(
        applicationName="EECodeDeploy",
        deploymentGroupName="EEDefaultDeploymentGroup",
    )
    asg_name = deployment_group["deploymentGroupInfo"]["autoScalingGroups"][0][
        "name"
    ]
    autoscale_client = session.client(
        "autoscaling", region_name=os.environ.get("AWS_REGION")
    )
    autoscale_client.describe_auto_scaling_groups(
        AutoScalingGroupNames=[asg_name]
    )["AutoScalingGroups"][0]
    asg_info = autoscale_client.describe_auto_scaling_groups(
        AutoScalingGroupNames=[asg_name]
    )["AutoScalingGroups"][0]
    instance_count = len(
        [i for i in asg_info["Instances"] if i["LifecycleState"] == "InService"]
    )

    if not instance_count:
        # There's no instances in this ASG, so we need to start one
        # before we can deploy
        autoscale_client.set_desired_capacity(
            AutoScalingGroupName=asg_name, DesiredCapacity=1
        )
        while instance_count < 1:
            time.sleep(5)
            print("Checking for ASG instances")
            asg_info = autoscale_client.describe_auto_scaling_groups(
                AutoScalingGroupNames=[asg_name]
            )["AutoScalingGroups"][0]
            instance_count = len(
                [
                    i
                    for i in asg_info["Instances"]
                    if i["LifecycleState"] == "InService"
                ]
            )

    print("ASG now has an instance running. Continuing with deploy")


def get_subnet_ids():
    """
    Returns a list of all subnet ids in the AWS account
    """
    client = session.client("ec2", region_name=os.environ.get("AWS_REGION"))
    response = client.describe_subnets()
    return [subnet["SubnetId"] for subnet in response["Subnets"]]


def get_target_group_arn():
    """
    Returns the arn of the ELB target group defined in sam-template.yaml
    """
    client = session.client("elbv2", region_name=os.environ.get("AWS_REGION"))
    response = client.describe_target_groups(Names=[TARGET_GROUP_NAME])
    return response["TargetGroups"][0]["TargetGroupArn"]


def create_default_asg():
    """
    Get or create the default auto scaling group
    """
    client = session.client(
        "autoscaling", region_name=os.environ.get("AWS_REGION")
    )
    subnet_ids = get_subnet_ids()
    target_group_arn = get_target_group_arn()
    existing_asgs = [
        asg["AutoScalingGroupName"]
        for asg in client.describe_auto_scaling_groups()["AutoScalingGroups"]
    ]
    if "default" in existing_asgs:
        return None

    min_size = 1
    max_size = 1
    desired_capacity = 1
    if os.environ.get("DC_ENVIRONMENT") == "production":
        min_size = 2
        max_size = 8
        desired_capacity = 2

    return client.create_auto_scaling_group(
        AutoScalingGroupName="default",
        AvailabilityZones=[
            "eu-west-2a",
            "eu-west-2b",
            "eu-west-2c",
        ],
        LaunchTemplate={
            "LaunchTemplateName": "ee-launch-template",
            "Version": "$Latest",
        },
        MinSize=min_size,
        MaxSize=max_size,
        DesiredCapacity=desired_capacity,
        HealthCheckType="ELB",
        HealthCheckGracePeriod=300,
        TargetGroupARNs=[target_group_arn],
        Tags=[
            {"Key": "CodeDeploy"},
            {"Key": "dc-product", "Value": "ee"},
            {
                "Key": "dc-environment",
                "Value": os.environ.get("DC_ENVIRONMENT"),
            },
        ],
        TerminationPolicies=[
            "OldestLaunchConfiguration",
            "ClosestToNextInstanceHour",
        ],
        VPCZoneIdentifier=",".join(subnet_ids),
    )


def get_service_role():
    """
    Use IAM client to return details of the CodeDeployServiceRole
    """
    client = boto3.client("iam", region_name=os.environ.get("AWS_REGION"))
    response = client.get_role(RoleName="CodeDeployServiceRole")
    return response["Role"]


def create_deployment_group():
    """
    Creates a default deployment group in CodeDeploy
    """
    client = session.client(
        "codedeploy", region_name=os.environ.get("AWS_REGION")
    )
    service_role = get_service_role()
    app_name = "EECodeDeploy"
    deployment_group_name = "EEDefaultDeploymentGroup"
    try:
        return client.get_deployment_group(
            applicationName=app_name,
            deploymentGroupName=deployment_group_name,
        )
    except client.exceptions.DeploymentGroupDoesNotExistException:
        return client.create_deployment_group(
            applicationName=app_name,
            deploymentGroupName=deployment_group_name,
            autoScalingGroups=[
                "default",
            ],
            deploymentConfigName="CodeDeployDefault.AllAtOnce",
            serviceRoleArn=service_role["Arn"],
            deploymentStyle={
                "deploymentType": "BLUE_GREEN",
                "deploymentOption": "WITH_TRAFFIC_CONTROL",
            },
            blueGreenDeploymentConfiguration={
                "terminateBlueInstancesOnDeploymentSuccess": {
                    "action": "TERMINATE",
                    "terminationWaitTimeInMinutes": 0,
                },
                "deploymentReadyOption": {
                    "actionOnTimeout": "CONTINUE_DEPLOYMENT",
                    # 'waitTimeInMinutes': 0
                },
                "greenFleetProvisioningOption": {
                    "action": "COPY_AUTO_SCALING_GROUP"
                },
            },
            loadBalancerInfo={
                "targetGroupInfoList": [{"name": TARGET_GROUP_NAME}],
            },
        )


def main():
    # check if we have a deployment group already, if so then we
    # assume codedeploy is already configured and nothing to do
    try:
        return check_deployment_group()
    except (ClientError, IndexError):
        pass

    # an error means this is likely the initial setup of a new account
    # so create the default ASG
    create_default_asg()
    # then create the default deployment group using that ASG
    create_deployment_group()
    # as this is an initial deployment wait a minute before moving on to next
    # step as the instance needs to have initialised and be in ready state
    # before code deploy can create a start deployment
    time.sleep(60)
    return None


if __name__ == "__main__":
    main()
