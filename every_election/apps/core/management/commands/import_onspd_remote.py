import os
import psutil
import shutil
import tempfile
import urllib.request
import sqlparse
from django.core.management.base import BaseCommand
from django.db import connection
from django.db import transaction
from storage.zipfile import unzip
from uk_geo_utils.management.commands.import_onspd import Command as LocalImporter
from uk_geo_utils.helpers import get_onspd_model


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cursor = connection.cursor()
        self.table_name = get_onspd_model()._meta.db_table
        self.temp_table_name = self.table_name + "_temp"

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

    def get_index_statements(self):
        self.cursor.execute(
            "SELECT indexdef FROM pg_indexes WHERE tablename='%s' ORDER BY indexname LIKE '%%_pk' DESC;"
            % (self.table_name)
        )
        results = self.cursor.fetchall()

        indexes = []
        statements = [row[0] for row in results]
        for statement in statements:
            indexes.append(
                {
                    "original_index_create_statement": statement,
                    "temp_index_create_statement": "",
                    "index_rename_statement": "",
                }
            )

        for index in indexes:
            index["temp_index_create_statement"] = index[
                "original_index_create_statement"
            ].replace(self.table_name, self.temp_table_name)
            parsed_sql = sqlparse.parse(index["original_index_create_statement"])[0]
            identifiers = [
                token.value
                for token in parsed_sql.tokens
                if not token.ttype and self.table_name in token.value
            ]
            if len(identifiers) != 2:
                raise Exception("Expected 2 identifiers, found %i" % len(identifiers))
            original_index_name = identifiers[0]
            temp_index_name = original_index_name.replace(
                self.table_name, self.temp_table_name
            )
            index["index_rename_statement"] = "ALTER INDEX %s RENAME TO %s" % (
                temp_index_name,
                original_index_name,
            )

        return indexes

    def create_temp_table(self):
        self.cursor.execute("DROP TABLE IF EXISTS %s;" % (self.temp_table_name))
        self.cursor.execute(
            "CREATE TABLE %s AS SELECT * FROM %s LIMIT 0;"
            % (self.temp_table_name, self.table_name)
        )

    def swap_tables(self):
        self.cursor.execute("DROP TABLE %s;" % (self.table_name))
        self.cursor.execute(
            "ALTER TABLE %s RENAME TO %s;" % (self.temp_table_name, self.table_name)
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
            self.stdout.write("Creating temp table..")
            self.create_temp_table()

            # import ONSPD into the temp table
            cmd = LocalImporter()
            cmd.table_name = self.temp_table_name
            cmd.path = data_path
            cmd.import_onspd()

            # grab the index CREATE statements from the old table before
            # we drop it. This will ensure we create the indexes on the
            # new table with the exact names django expects them to have
            # (e.g: uk_geo_utils_onspd_pcds_9d376544_uniq )
            # so we can still run migrations and stuff on it
            indexes = self.get_index_statements()

            self.stdout.write("Building indexes..")
            for index in indexes:
                self.cursor.execute(index["temp_index_create_statement"])

            # drop the old table, swap in the new one and rename the indexes
            # do this bit in a transaction so if it fails
            # we don't leave ourselves in an inconsistent state
            with transaction.atomic():
                self.stdout.write("Swapping tables..")
                self.swap_tables()

                self.stdout.write("Renaming indexes..")
                for index in indexes:
                    self.cursor.execute(index["index_rename_statement"])

        finally:
            self.cursor.execute("DROP TABLE IF EXISTS %s;" % (self.temp_table_name))
            self.stdout.write("Cleaning up temp files..")
            self.cleanup(tempdir)

        self.stdout.write("...done")

    def cleanup(self, tempdir):
        # clean up the temp files we created
        try:
            shutil.rmtree(tempdir)
        except OSError:
            self.stdout.write("Failed to clean up temp files.")
