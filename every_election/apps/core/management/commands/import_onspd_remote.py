import os
import psutil
import shutil
import tempfile
import urllib.request
from django.core.management.base import BaseCommand
from django.db import connection
from django.db import transaction
from storage.zipfile import unzip
from uk_geo_utils.management.commands.import_onspd import Command as LocalImporter
from uk_geo_utils.helpers import get_onspd_model


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("url", action="store")

    def check_memory(self):
        # Downloading, unzipping and working with the ONSPD
        # requires a decent chunk of memory to play with.
        # Running this import on a really small instance
        # like a t2.micro will cause an Out Of Memory error

        # Ensure we've got >2Gb total before we start
        mem = psutil.virtual_memory()
        gb = ((mem.total / 1024) / 1024) / 1024
        return gb >= 2

    def get_index_create_statements(self, table_name):
        cursor = connection.cursor()
        cursor.execute(
            "SELECT indexdef FROM pg_indexes WHERE tablename='%s';" % (table_name)
        )
        results = cursor.fetchall()
        return [row[0] for row in results]

    def create_temp_table(self, table_name, temp_table_name):
        cursor = connection.cursor()
        cursor.execute("DROP TABLE IF EXISTS %s;" % (temp_table_name))
        cursor.execute(
            "CREATE TABLE %s AS SELECT * FROM %s LIMIT 0;"
            % (temp_table_name, table_name)
        )

    def swap_tables(self, table_name, temp_table_name):
        cursor = connection.cursor()
        # drop the old table and swap in the new one
        # do these 2 in a transaction so if it fails
        # we don't leave ourselves in an inconsistent state
        with transaction.atomic():
            cursor.execute("DROP TABLE %s;" % (table_name))
            cursor.execute(
                "ALTER TABLE %s RENAME TO %s;" % (temp_table_name, table_name)
            )

    def handle(self, **options):
        if not self.check_memory():
            raise Exception(
                "This instance has less than the recommended memory. Try running the import from a larger instance."
            )

        url = options["url"]
        self.stdout.write("Downloading data from %s ..." % (url))
        tmp = tempfile.NamedTemporaryFile()
        urllib.request.urlretrieve(url, tmp.name)
        tempdir = unzip(tmp.name)
        data_path = os.path.join(tempdir, "Data")

        try:
            table_name = get_onspd_model()._meta.db_table
            temp_table_name = table_name + "_temp"
            self.stdout.write("Creating temp table..")
            self.create_temp_table(table_name, temp_table_name)

            # import ONSPD into the temp table
            cmd = LocalImporter()
            cmd.table_name = temp_table_name
            cmd.path = data_path
            cmd.import_onspd()

            # grab the index CREATE statements from the old table before
            # we drop it. This will ensure we create the indexes on the
            # new table with the exact names django expects them to have
            # (e.g: uk_geo_utils_onspd_pcds_9d376544_uniq )
            # so we can still run migrations and stuff on it
            index_create_statements = self.get_index_create_statements(table_name)

            self.stdout.write("Swapping tables..")
            self.swap_tables(table_name, temp_table_name)

            # create the indexes outside of the transaction block
            # this will mean we block queries for the absolute minimum time
            # the table will be queryable (but a bit slower) while the indexes rebuild
            self.stdout.write("Building indexes..")
            cursor = connection.cursor()
            for statement in index_create_statements:
                cursor.execute(statement)
        finally:
            self.stdout.write("Cleaning up temp files..")
            self.cleanup(tempdir)
        self.stdout.write("...done")

    def cleanup(self, tempdir):
        # clean up the temp files we created
        try:
            shutil.rmtree(tempdir)
        except OSError:
            self.stdout.write("Failed to clean up temp files.")
