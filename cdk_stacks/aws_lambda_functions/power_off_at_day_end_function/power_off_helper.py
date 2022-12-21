"""
Powers off servers when called.

"""
import random
import time

import boto3


def reduce_alb_size(tag_name, tag_value, at_most=0, region="eu-west-2"):
    client = boto3.client("autoscaling", region_name=region)
    asg_list = client.describe_auto_scaling_groups(
        Filters=[{"Name": f"tag:{tag_name}", "Values": [tag_value]}]
    )["AutoScalingGroups"]

    for asg in asg_list:
        name = asg["AutoScalingGroupName"]
        for tag in asg["Tags"]:
            if tag["Key"] == "dc-environment":
                if tag["Value"] == "production":
                    print(f"Not touching {name} as it's a production ASG")
                    continue
        print(f"Updating {name} to MinSize={at_most} DesiredCapacity={at_most}")
        client.update_auto_scaling_group(
            AutoScalingGroupName=name,
            MinSize=at_most,
            DesiredCapacity=at_most,
        )


if __name__ == "__main__":
    # Use for debugging and ad-hoc commands
    reduce_alb_size(tag_name="dc-product", tag_value="ee")
