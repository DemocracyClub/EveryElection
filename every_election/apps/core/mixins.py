import csv
import re
import tempfile
import urllib

import requests
from django_extensions.db.models import TimeStampedModel

from storage.s3wrapper import S3Wrapper


"""
Generic mixins for reading from files in a Django management command.
The files can be a local file, a URL or on an S3 bucket.
`self.S3_BUCKET_NAME` needs to be set when using S3.
"""


class ReadFromFileMixin:

    S3_BUCKET_NAME = None

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "-f", "--file", action="store", help="Path to import e.g: /foo/bar/baz.csv"
        )
        group.add_argument(
            "-u",
            "--url",
            action="store",
            help="URL to import e.g: http://foo.bar/baz.csv",
        )
        group.add_argument(
            "-s", "--s3", action="store", help="S3 key to import e.g: foo/bar/baz.csv"
        )

    def read_from_local(self, filename):
        return open(filename, "rt")

    def read_from_url(self, url):
        tmp = tempfile.NamedTemporaryFile()
        urllib.request.urlretrieve(url, tmp.name)
        return tmp

    def read_from_s3(self, filepath):
        s3 = S3Wrapper(self.S3_BUCKET_NAME)
        return s3.get_file(filepath)

    def load_data(self, options):
        if options["file"]:
            return self.read_from_local(options["file"])
        if options["url"]:
            return self.read_from_url(options["url"])
        if options["s3"]:
            return self.read_from_s3(options["s3"])


class ReadFromCSVMixin(ReadFromFileMixin):

    ENCODING = "utf-8"
    DELIMITER = ","

    def read_from_local(self, filename):
        f = open(filename, "rt", encoding=self.ENCODING)
        reader = csv.DictReader(f, delimiter=self.DELIMITER)
        return list(reader)

    def read_from_url(self, url):
        r = requests.get(url)
        r.raise_for_status()

        # if CSV came from google docs
        # manually set the encoding
        gdocs_pattern = r"(.)+docs\.google(.)+\/ccc(.)+"
        if re.match(gdocs_pattern, url):
            r.encoding = self.ENCODING

        csv_reader = csv.DictReader(r.text.splitlines())
        return list(csv_reader)

    def read_from_s3(self, filepath):
        f = super().read_from_s3(filepath)
        return self.read_from_local(f.name)


class UpdateElectionsTimestampedModel(TimeStampedModel):
    class Meta:
        get_latest_by = "modified"
        abstract = True

    def save(self, **kwargs):
        """
        Whenever the object is saved, we update all related elections
        modified date to have the same date. This is to make sure that
        changes made on the parent Organisation or
        OrganisationDivision are picked up by importers looking for
        changes to the Election made in EE
        """
        super().save(**kwargs)
        self.election_set.update(modified=self.modified)
