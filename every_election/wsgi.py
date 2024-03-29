import os
from os.path import abspath, dirname
from sys import path

import dotenv
from django.core.wsgi import get_wsgi_application

"""
WSGI config for every_election project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""


SITE_ROOT = dirname(dirname(abspath(__file__)))
path.append(SITE_ROOT)

dotenv.read_dotenv(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "every_election.settings")

application = get_wsgi_application()
