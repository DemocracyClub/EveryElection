#!/usr/bin/env python3
import os

from aws_cdk import core as cdk
from aws_cdk.core import Tags

from cdk_stacks.stacks.code_deploy import EECodeDeployment
from cdk_stacks.stacks.command_runner import EEOncePerTagCommandRunner
from cdk_stacks.stacks.image_builder import EEImageUpdater
from cdk_stacks.stacks.power_off_at_end_of_day import PowerOffAtEndOfDay

valid_environments = (
    "development",
    "staging",
    "production",
)

app_wide_context = {}
if dc_env := os.environ.get("DC_ENVIRONMENT"):
    app_wide_context["dc-environment"] = dc_env

app = cdk.App(context=app_wide_context)

env = cdk.Environment(account=os.getenv("CDK_DEFAULT_ACCOUNT"), region="eu-west-2")

# Set the DC Environment early on. This is important to be able to conditionally
# change the stack configurations
dc_environment = app.node.try_get_context("dc-environment") or None
assert (
    dc_environment in valid_environments
), f"context `dc-environment` must be one of {valid_environments}"

if dc_environment == "production":
    EEImageUpdater(
        app,
        "EEImageUpdater",
        env=env,
    )
EECodeDeployment(app, "EECodeDeployment", env=env)

EEOncePerTagCommandRunner(app, "EEOncePerTagCommandRunner", env=env)

if dc_environment != "production":
    PowerOffAtEndOfDay(app, "PowerOffAtEndOfDay", env=env)


Tags.of(app).add("dc-product", "ee")
Tags.of(app).add("dc-environment", dc_environment)

app.synth()
