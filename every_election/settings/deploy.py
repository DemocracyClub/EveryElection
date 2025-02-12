# deploy.py
# The default settings entrypoint
# Set things here that we want to be true in ALL deployed environments
# but don't make sense in local dev

from .base import *  # noqa

DEBUG = False
