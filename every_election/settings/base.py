import os
import sys

import dc_design_system

# PATH vars

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root = lambda *x: os.path.join(BASE_DIR, *x)

sys.path.insert(0, root("apps"))


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "CHANGE THIS!!!"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
IN_TESTING = sys.argv[1:2] == ["test"]

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_filters",
    "dc_signup_form",
    "corsheaders",
    "uk_geo_utils",
    "dc_design_system",
]

PROJECT_APPS = [
    "api",
    "core",
    "dc_theme",
    "elections",
    "organisations",
    "organisations.boundaries",
    "rest_framework",
    # 'static_precompiler',
    "pipeline",
    "storages",
    "django_extensions",
    "election_snooper",
]

INSTALLED_APPS += PROJECT_APPS

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "null": {"class": "logging.NullHandler"},
    },
    "loggers": {
        # Silence DisallowedHost exception by setting null error handler
        "django.security.DisallowedHost": {"handlers": ["null"], "propagate": False},
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
    },
}

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django_middleware_global_request.middleware.GlobalRequestMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.BasicAuthMiddleware",
]

ROOT_URLCONF = "every_election.urls"

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = "every_election.wsgi.application"

# Database

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "every_election",
        "USER": "postgres",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    }
}

# Internationalization

LANGUAGE_CODE = "en-gb"

TIME_ZONE = "UTC"

USE_I18N = False

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"

# Additional locations of static files

STATICFILES_DIRS = (root("assets"),)

STATIC_ROOT = root("static")


from dc_theme.settings import get_pipeline_settings
from dc_theme.settings import STATICFILES_STORAGE, STATICFILES_FINDERS  # noqa


PIPELINE = get_pipeline_settings(
    extra_css=["css/styles.scss"], extra_js=["js/date.format.js"]
)

PIPELINE["SASS_ARGUMENTS"] += " -I " + dc_design_system.DC_SYSTEM_PATH + "/system"

INTERNAL_IPS = ("127.0.0.1",)


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": [root("templates")],
        "OPTIONS": {
            "debug": DEBUG,
            "context_processors": [
                "dc_theme.context_processors.dc_theme_context",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.request",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "dc_signup_form.context_processors.signup_form",
                "core.context_processors.global_settings",
            ],
        },
    }
]

# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

DATA_UPLOAD_MAX_NUMBER_FIELDS = None

SITE_TITLE = "Every Election"

DATA_CACHE_DIR = root("data_cache")


LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"


REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 100,
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
        "rest_framework_jsonp.renderers.JSONPRenderer",
    ),
}

CORS_ORIGIN_ALLOW_ALL = True
CORS_URLS_REGEX = r"^/api/.*$"
CORS_ALLOW_METHODS = ("GET", "OPTIONS")

UPSTREAM_SYNC_URL = "https://elections.democracyclub.org.uk/sync/"


NOTICE_OF_ELECTION_BUCKET = "notice-of-election"
LGBCE_BUCKET = "lgbce-mirror"

AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""
AWS_S3_REGION_NAME = "eu-west-1"

# django-storages expects AWS_STORAGE_BUCKET_NAME
AWS_STORAGE_BUCKET_NAME = NOTICE_OF_ELECTION_BUCKET
# versioning is on so we can retreive old copies
AWS_S3_FILE_OVERWRITE = True
AWS_DEFAULT_ACL = None


EMAIL_SIGNUP_ENDPOINT = "https://democracyclub.org.uk/mailing_list/api_signup/v1/"
EMAIL_SIGNUP_API_KEY = ""


# Disable Basic Auth by default
# We only want to use this on staging deploys
BASICAUTH_DISABLE = True


# elections where polling day is in the range
# (NOW - CURRENT_PAST_DAYS) - (NOW + CURRENT_FUTURE_DAYS)
# are considered "current"
CURRENT_PAST_DAYS = 20
CURRENT_FUTURE_DAYS = 90


# .local.py overrides all the common settings.
try:
    from .local import *  # noqa
except ImportError:
    pass


# importing test settings file if necessary
if IN_TESTING:
    from .testing import *  # noqa

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
