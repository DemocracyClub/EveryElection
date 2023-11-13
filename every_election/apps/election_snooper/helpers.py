import json
import os
import textwrap
import warnings

import requests
from django.conf import settings


def post_to_slack(message):
    if not getattr(settings, "SLACK_WEBHOOK_URL", None):
        if not settings.DEBUG:
            warnings.warn("settings.SLACK_WEBHOOK_URL is not set")
        return

    env = os.getenv(
        "SERVER_ENVIRONMENT", getattr(settings, "SERVER_ENVIRONMENT", None)
    )
    if env in ["test", "development", "staging"]:
        prefix = "TEST for {} environment: ".format(env)
        message = prefix + message

    url = settings.SLACK_WEBHOOK_URL

    payload = {
        "icon_emoji": ":satellite_antenna:",
        "username": "Election Radar",
        "text": textwrap.dedent(message),
    }

    requests.post(url, json.dumps(payload), timeout=2)
