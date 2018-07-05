import shutil

from django.core.management.base import BaseCommand
from core.mixins import ReadFromFileMixin
from storage.zipfile import unzip


class BaseBoundaryLineCommand(ReadFromFileMixin, BaseCommand):

    def get_base_dir(self, **options):
        try:
            if options['url']:
                self.stdout.write('Downloading data from %s ...' % (options['url']))
            fh = self.load_data(options)
            self.stdout.write('Extracting archive...')
            path = unzip(fh.name)
            self.stdout.write('...done')

            # if we've extracted a zip file to a temp location
            # we want to delete the temp files when we're done
            self.cleanup_required = True
            return path
        except IsADirectoryError:
            return options['file']

    def cleanup(self, tempdir):
        # clean up the temp files we created
        try:
            shutil.rmtree(tempdir)
        except OSError:
            self.stdout.write("Failed to clean up temp files.")
