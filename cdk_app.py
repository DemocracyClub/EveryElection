#!/usr/bin/env python3
import os

from aws_cdk import core as cdk

from cdk_imagebuilder.stacks.image_builder import EEImageUpdater

app = cdk.App()

EEImageUpdater(
    app,
    "EEImageUpdater",
    env=cdk.Environment(account=os.getenv("CDK_DEFAULT_ACCOUNT"), region="eu-west-2"),
)


app.synth()
