import tempfile
import urllib.request
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        url = settings.UPSTREAM_SYNC_URL
        with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
            urllib.request.urlretrieve(url, tmp.name)
            call_command("loaddata", tmp.name)
