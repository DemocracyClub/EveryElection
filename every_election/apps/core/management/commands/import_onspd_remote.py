import os
import psutil
import shutil
import tempfile
import urllib.request
from django.core.management.base import BaseCommand
from storage.zipfile import unzip
from uk_geo_utils.management.commands.import_onspd import Command as LocalImporter


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('url', action='store')

    def check_memory(self):
        # Downloading, unzipping and working with the ONSPD
        # requires a decent chunk of memory to play with.
        # Running this import on a really small instance
        # like a t2.micro will cause an Out Of Memory error

        # Ensure we've got >2Gb total before we start
        mem = psutil.virtual_memory()
        gb = (((mem.total/1024)/1024)/1024)
        return gb >= 2

    def handle(self, **options):
        if not self.check_memory():
            raise Exception(
                'This instance has less than the recommended memory. Try running the import from a larger instance.'
            )

        url = options['url']
        self.stdout.write('Downloading data from %s ...' % (url))
        tmp = tempfile.NamedTemporaryFile()
        urllib.request.urlretrieve(url, tmp.name)
        tempdir = unzip(tmp.name)
        data_path = os.path.join(tempdir, 'Data')
        try:
            cmd = LocalImporter()
            cmd.handle(**{ 'path': data_path, 'transaction': False })
        finally:
            self.cleanup(tempdir)

    def cleanup(self, tempdir):
        # clean up the temp files we created
        try:
            shutil.rmtree(tempdir)
        except OSError:
            self.stdout.write("Failed to clean up temp files.")
