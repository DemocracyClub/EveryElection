# testing.py
# Set things here that we want to always be true when running unit tests

import os

from .base import *  # noqa

print("loading TESTING settings")
print("---")

IN_TESTING = True

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
