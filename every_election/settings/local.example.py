DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    }
}

# google custom search API key
GCS_API_KEY = ""

# don't use the real url in dev or staging
# there is a webhook url for each environment, so
# we can test the slack integration
SLACK_WEBHOOK_URL = ""

# AWS credentials
AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""

# don't use the real bucket in dev
AWS_STORAGE_BUCKET_NAME = "notice-of-election-dev"

# using cache sessions instead of database sessions
# in dev makes it easier to debug the wizard
SESSION_ENGINE = "django.contrib.sessions.backends.cache"

# Turn Debug tool bar on or off
DEBUG_TOOLBAR = True
