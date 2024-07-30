import aws_cdk.aws_lambda_python_alpha as aws_lambda_python
from aws_cdk import (
    Duration,
    Stack,
    aws_events,
    aws_events_targets,
    aws_iam,
    aws_lambda,
)
from constructs import Construct


class EEOncePerTagCommandRunner(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        role = aws_iam.Role(
            self,
            "OncePerTagCommandRunnerRole",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            max_session_duration=Duration.hours(1),
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

        self.once_per_tag_command_runner = aws_lambda_python.PythonFunction(
            self,
            "once_per_tag_command_runner",
            function_name="once_per_tag_command_runner",
            entry="./cdk_stacks/aws_lambda_functions/ssm_run_command_once",
            index="main.py",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.minutes(2),
            role=role,
        )

        # Environment conditionals
        dc_environment = (
            self.node.try_get_context("dc-environment") or "development"
        )

        if dc_environment == "production":
            # Back-ups
            self.add_job(
                "backup_to_s3",
                "cron(30 1 * * ? *)",
                "output-on-error /var/www/every_election/repo/serverscripts/backup_db_to_s3.sh",
            )

            # New elections
            # self.add_job(
            #     "snoop",
            #     "cron(30 * * * ? *)",
            #     "output-on-error ee-manage-py-command snoop",
            # )

            # Generate map layers and sync to S3
            self.add_job(
                "sync_map_layers_to_s3",
                "cron(40 1 * * ? *)",
                "output-on-error /var/www/every_election/repo/serverscripts/sync_map_layers_to_s3.sh",
            )

            # Add NUTS1 tags to any new elections
            self.add_job(
                "add_nuts1_tags",
                "cron(15 2 * * ? *)",
                """output-on-error ee-manage-py-command add_tags -u "https://s3.eu-west-2.amazonaws.com/ee.public.data/ons-cache/NUTS_Level_1_(January_2018)_Boundaries.gpkg" --fields '{"NUTS118NM": "value", "NUTS118CD": "key"}' --tag-name NUTS1 --is-gpkg""",
            )

            # Scrape LGBCE
            self.add_job(
                "scrape_lgbce",
                "cron(16 7 * * ? *)",
                "output-on-error ee-manage-py-command scrape_lgbce",
            )

            # Export WKT Ballots
            self.add_job(
                "export_wkt_ballots",
                "cron(30 2 * * ? *)",
                f"output-on-error ee-manage-py-command export_ballots_as_wkt_csv --bucket 'ee.data-cache.{dc_environment}' --prefix 'ballots-with-wkt'",
            )

    def add_job(
        self,
        command_name,
        schedule_expression,
        command,
        tag_name="dc-product",
        tag_value="ee",
    ):
        _command = aws_events.Rule(
            self,
            command_name,
            rule_name=command_name,
            schedule=aws_events.Schedule.expression(schedule_expression),
        )
        _command.add_target(
            aws_events_targets.LambdaFunction(
                handler=self.once_per_tag_command_runner,
                event=aws_events.RuleTargetInput.from_object(
                    {
                        "tag_name": tag_name,
                        "tag_value": tag_value,
                        "command": command,
                    }
                ),
            )
        )
