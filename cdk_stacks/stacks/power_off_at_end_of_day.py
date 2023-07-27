"""
Automate shutting off servers and other resources and the end of the day.

A new deploy will being the servers back again, or it's possible to manually enable the resources.

"""

from aws_cdk import (
    aws_events,
    aws_events_targets,
    aws_iam,
    aws_lambda,
    aws_lambda_python,
    core,
)
from aws_cdk.core import Construct, Stack


class PowerOffAtEndOfDay(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        role = aws_iam.Role(
            self,
            "PowerOffAtEndOfDay",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            max_session_duration=core.Duration.hours(1),
        )
        for managed_policy_arn in [
            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
            "arn:aws:iam::aws:policy/AmazonEC2FullAccess",
        ]:
            managed_policy = aws_iam.ManagedPolicy.from_managed_policy_arn(
                self,
                managed_policy_arn.split("/")[-1],
                managed_policy_arn=managed_policy_arn,
            )
            role.add_managed_policy(managed_policy)

        power_off_at_day_end_function = aws_lambda_python.PythonFunction(
            self,
            "power_off_at_day_end_function",
            function_name="power_off_at_day_end_function",
            entry="./cdk_stacks/aws_lambda_functions/power_off_at_day_end_function",
            index="main.py",
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            timeout=core.Duration.minutes(10),
            role=role,
        )

        # Environment conditionals
        dc_environment = self.node.try_get_context("dc-environment")

        if dc_environment != "production":
            # Set up the rules we want
            power_off_event = aws_events.Rule(
                self,
                "power_off_event",
                rule_name="power_off_event",
                schedule=aws_events.Schedule.expression("cron(30 22 * * ? *)"),
            )
            power_off_event.add_target(
                aws_events_targets.LambdaFunction(
                    handler=power_off_at_day_end_function,
                    event=aws_events.RuleTargetInput.from_object(
                        {
                            "tag_name": "dc-product",
                            "tag_value": "ee",
                            "at_most": "0",
                        }
                    ),
                )
            )
