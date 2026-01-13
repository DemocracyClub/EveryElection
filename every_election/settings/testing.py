# testing.py
# Set things here that we want to always be true when running unit tests

import os

from .base import *  # noqa

IN_TESTING = True

# override these settings to safe values if they are set from the env
SEND_EVENTS = False
GCS_API_KEY = ""
SLACK_WEBHOOK_URL = ""
AWS_STORAGE_BUCKET_NAME = "notice-of-election-dev"
LGBCE_BUCKET = None


os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
