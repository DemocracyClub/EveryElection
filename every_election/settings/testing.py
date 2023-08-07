import os

from .base import *  # noqa

IN_TESTING = True
DEBUG = True

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
