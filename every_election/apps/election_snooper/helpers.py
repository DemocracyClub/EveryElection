import json
import os
import textwrap
import warnings

from django.conf import settings

import requests


def post_to_slack(message):
    env = os.getenv(
        "SERVER_ENVIRONMENT", getattr(settings, "SERVER_ENVIRONMENT", None)
    )
    if env in ["test", "development", "staging"]:
        prefix = "TEST for {} environment: ".format(env)
        message = prefix + message
    url = settings.SLACK_WEBHOOK_URL

    if not hasattr(settings, "SLACK_WEBHOOK_URL") and env == "production":
        warnings.warn("settings.SLACK_WEBHOOK_URL is not set")
        return
    if not hasattr(settings, "SLACK_WEBHOOK_URL") and env in [
        "test",
        "development",
        "staging",
    ]:
        print("SLACK_WEBHOOK_URL is not set")

    payload = {
        "icon_emoji": ":satellite_antenna:",
        "username": "Election Radar",
        "text": textwrap.dedent(message),
    }

    requests.post(url, json.dumps(payload), timeout=2)
