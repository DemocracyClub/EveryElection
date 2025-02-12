import os
import sys

import dc_design_system
import requests
from dc_utils.settings.pipeline import *  # noqa
from dc_utils.settings.pipeline import get_pipeline_settings
from dc_utils.settings.whitenoise import whitenoise_add_middleware

# PATH vars

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def root(*x):
    return os.path.join(BASE_DIR, *x)


sys.path.insert(0, root("apps"))


def str_bool_to_bool(str_bool):
    if not str_bool:
        return False
    return str_bool in ["1", "True", "true", "TRUE"]


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("EE_SECRET_KEY", "CHANGE THIS!!!")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", None)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
IN_TESTING = sys.argv[1:2] == "test" or sys.argv[0].endswith("pytest")

ALLOWED_HOSTS = [
    os.environ.get("FQDN", None),
    "localhost",
    "127.0.0.1",
]


def get_ec2_ip():
    token_req = requests.put(
        "http://169.254.169.254/latest/api/token",
        headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
        timeout=2,
    )
    token_req.raise_for_status()
    token_req.text
    ip_req = requests.get(
        "http://169.254.169.254/latest/meta-data/local-ipv4",
        headers={"X-aws-ec2-metadata-token": token_req.text},
        timeout=2,
    )
    ip_req.raise_for_status()
    return ip_req.text


if os.environ.get("DC_ENVIRONMENT"):
    ALLOWED_HOSTS.append(get_ec2_ip())

USE_X_FORWARDED_HOST = True

if fqdn := os.environ.get("FQDN"):
    CSRF_TRUSTED_ORIGINS = [
        f"https://{fqdn}",
    ]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_filters",
    "corsheaders",
    "uk_geo_utils",
    "dc_design_system",
    "whitenoise",
]

PROJECT_APPS = [
    "api",
    "core",
    "elections",
    "organisations",
    "organisations.boundaries",
    "rest_framework",
    "pipeline",
    "storages",
    "django_extensions",
    "election_snooper",
    "dc_utils",
]

INSTALLED_APPS += PROJECT_APPS

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}
    },
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
        "django.security.DisallowedHost": {
            "handlers": ["null"],
            "propagate": False,
        },
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
    "dc_utils.middleware.BasicAuthMiddleware",
]

ROOT_URLCONF = "every_election.urls"

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = "every_election.wsgi.application"

# Database

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.environ.get("EE_DATABASE_NAME", "every_election"),
        "USER": os.environ.get("EE_DATABASE_USER", "every_election"),
        "PASSWORD": os.environ.get("EE_DATABASE_PASSWORD", ""),
        "HOST": os.environ.get("EE_DATABASE_HOST", ""),
        "PORT": os.environ.get("EE_DATABASE_PORT", ""),
        "CONN_MAX_AGE": 0,
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

STATICFILES_DIRS = (root("assets"), root("../node_modules"))
STATIC_ROOT = root("static")

MIDDLEWARE = whitenoise_add_middleware(MIDDLEWARE)
WHITENOISE_MAX_AGE = 60 * 60 * 24 * 40

PIPELINE = get_pipeline_settings(
    extra_css=["scss/styles.scss"],
    extra_js=["js/date.format.js", "js/scripts.js"],
)

PIPELINE["SASS_ARGUMENTS"] += (
    " -I " + dc_design_system.DC_SYSTEM_PATH + "/system"
)

PIPELINE["STYLESHEETS"].update(
    {
        "map": {
            "source_filenames": [
                "leaflet/dist/leaflet.css",
            ],
            "output_filename": "css/map.css",
        },
    }
)

PIPELINE["JAVASCRIPT"].update(
    {
        "map": {
            "source_filenames": [
                "leaflet/dist/leaflet.js",
            ],
            "output_filename": "js/map.js",
        }
    }
)

INTERNAL_IPS = ("127.0.0.1",)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": [root("templates")],
        "OPTIONS": {
            "debug": DEBUG,
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.request",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "core.context_processors.global_settings",
                "dc_utils.context_processors.dc_django_utils",
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
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"
    },
]

DATA_UPLOAD_MAX_NUMBER_FIELDS = None

SITE_TITLE = "Every Election"

DATA_CACHE_DIR = root("data_cache")

LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "core.helpers.MaxSizeLimitOffsetPagination",
    "PAGE_SIZE": 100,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
        "rest_framework_jsonp.renderers.JSONPRenderer",
    ),
}
API_MAX_LIMIT = 100

CORS_ORIGIN_ALLOW_ALL = True
CORS_URLS_REGEX = r"^/api/.*$"
CORS_ALLOW_METHODS = ("GET", "OPTIONS")

UPSTREAM_SYNC_URL = "https://elections.democracyclub.org.uk/api/elections/"
GCS_API_KEY = os.environ.get("GCS_API_KEY", "")

NOTICE_OF_ELECTION_BUCKET = "notice-of-election"
LGBCE_BUCKET = os.environ.get("BOUNDARY_REVIEW_BUCKET", None)

# django-storages expects AWS_STORAGE_BUCKET_NAME
AWS_STORAGE_BUCKET_NAME = NOTICE_OF_ELECTION_BUCKET
# versioning is on so we can retreive old copies
AWS_S3_FILE_OVERWRITE = True
AWS_DEFAULT_ACL = None

# Allowlist of URLs that should be ignored by DC BasicAuthMiddleware
BASIC_AUTH_ALLOWLIST = [
    "/",  # load balancer health check
    "/api",
    "/api/*",
]

# elections where polling day is in the range
# (NOW - CURRENT_PAST_DAYS) - (NOW + CURRENT_FUTURE_DAYS)
# are considered "current"
CURRENT_PAST_DAYS = 20
CURRENT_FUTURE_DAYS = 90

DEBUG_TOOLBAR = False

if not os.environ.get("DC_ENVIRONMENT") and DEBUG_TOOLBAR:
    INSTALLED_APPS += ("debug_toolbar",)
    MIDDLEWARE = [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ] + MIDDLEWARE

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

if sentry_dsn := os.environ.get("SENTRY_DSN"):
    import sentry_sdk
    from sentry_sdk.integrations import django
    from sentry_sdk.integrations.logging import ignore_logger

    ignore_logger("django.security.DisallowedHost")

    sentry_sdk.init(
        dsn=sentry_dsn,
        # Disable performance monitoring
        enable_tracing=False,
        integrations=[
            django.DjangoIntegration(),
        ],
        environment=os.environ.get("DC_ENVIRONMENT"),
    )
