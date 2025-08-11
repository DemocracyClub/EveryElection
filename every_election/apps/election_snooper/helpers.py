import json
import os
import textwrap
import warnings
from typing import Any, Dict, List, Optional

import requests
from django.conf import settings


def post_to_slack(
    message=None,
    username="Election Radar",
    icon_emoji=":satellite_antenna:",
    blocks: Optional[List[Dict[str, Any]]] = None,
):
    if all((message, blocks)):
        raise ValueError("Can't use both message and blocks. Pick one.")

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

    payload: Dict[str, Any] = {
        "icon_emoji": icon_emoji,
        "username": username,
    }

    if isinstance(blocks, list):
        payload["blocks"] = blocks
    else:
        payload["text"] = textwrap.dedent(message)

    requests.post(url, json.dumps(payload), timeout=2)
