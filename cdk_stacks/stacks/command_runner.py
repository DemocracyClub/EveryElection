from aws_cdk import (
    aws_events,
    aws_events_targets,
    aws_lambda,
    aws_lambda_python,
    aws_iam,
    core,
)
from aws_cdk.core import Construct, Stack


class EEOncePerTagCommandRunner(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        role = aws_iam.Role(
            self,
            "OncePerTagCommandRunnerRole",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            max_session_duration=core.Duration.hours(1),
        )
        for managed_policy_arn in [
            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
            "arn:aws:iam::aws:policy/AmazonSSMFullAccess",
            "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess",
        ]:
            managed_policy = aws_iam.ManagedPolicy.from_managed_policy_arn(
                self,
                managed_policy_arn.split("/")[-1],
                managed_policy_arn=managed_policy_arn,
            )
            role.add_managed_policy(managed_policy)

        once_per_tag_command_runner = aws_lambda_python.PythonFunction(
            self,
            "once_per_tag_command_runner",
            function_name="once_per_tag_command_runner",
            entry="./cdk_stacks/aws_lambda_functions/ssm_run_command_once",
            index="main.py",
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            timeout=core.Duration.minutes(2),
            role=role,
        )

        # Environment conditionals
        dc_environment = self.node.try_get_context("dc-environment") or "development"

        if dc_environment == "production":
            # Set up the rules we want
            backup_prod_rds_to_s3 = aws_events.Rule(
                self,
                "backup_prod_rds_to_s3",
                rule_name="backup_prod_rds_to_s3",
                schedule=aws_events.Schedule.expression("cron(30 1 * * ? *)"),
            )
            backup_prod_rds_to_s3.add_target(
                aws_events_targets.LambdaFunction(
                    handler=once_per_tag_command_runner,
                    event=aws_events.RuleTargetInput.from_object(
                        {
                            "tag_name": "dc-product",
                            "tag_value": "ee",
                            "command": "ls -la /",
                        }
                    ),
                )
            )
