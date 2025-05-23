# dev.py
# Set things here that we want to always be true in dev
# but don't make sense in any deployed environment

from .base import *  # noqa
import contextlib

DEBUG = True

INSTALLED_APPS += ("debug_toolbar",)  # noqa: F405
MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
] + MIDDLEWARE  # noqa: F405

# using cache sessions instead of database sessions
# in dev makes it easier to debug the wizard
SESSION_ENGINE = "django.contrib.sessions.backends.cache"

# don't use the real bucket in dev
AWS_STORAGE_BUCKET_NAME = "notice-of-election-dev"

with contextlib.suppress(ImportError):
    from .local import *  # noqa
