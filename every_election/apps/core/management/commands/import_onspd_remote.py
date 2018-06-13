import os
import shutil
import tempfile
import urllib.request
from django.core.management.base import BaseCommand
from storage.zipfile import unzip
from uk_geo_utils.management.commands.import_onspd import Command as LocalImporter


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('url', action='store')

    def handle(self, **options):
        url = options['url']
        self.stdout.write('Downloading data from %s ...' % (url))
        tmp = tempfile.NamedTemporaryFile()
        urllib.request.urlretrieve(url, tmp.name)
        tempdir = unzip(tmp.name)
        data_path = os.path.join(tempdir, 'Data')
        try:
            cmd = LocalImporter()
            cmd.handle(**{ 'path': data_path })
        finally:
            self.cleanup(tempdir)

    def cleanup(self, tempdir):
        # clean up the temp files we created
        try:
            shutil.rmtree(tempdir)
        except OSError:
            self.stdout.write("Failed to clean up temp files.")
