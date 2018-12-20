import json
import textwrap
import warnings

from django.conf import settings

import requests


def post_to_slack(message):
    if not hasattr(settings, 'SLACK_WEBHOOK_URL'):
        warnings.warn("settings.SLACK_WEBHOOK_URL is not set")
        return

    payload = {
        "icon_emoji": ":satellite_antenna:",
        "username": "Election Radar",
        "text": textwrap.dedent(message),
    }
    url = settings.SLACK_WEBHOOK_URL
    requests.post(url, json.dumps(payload), timeout=2)
