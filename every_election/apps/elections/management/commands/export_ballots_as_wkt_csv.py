import csv
import datetime
import io

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


def export_sql(date: str):
    return f"""
    SELECT
        ee.election_id,
        COALESCE(odd.id, ogd.id) AS geography_id,
        COALESCE(st_astext(odd.geography), st_astext(ogd.geography)) AS geography_text,
        CASE
           WHEN ogd.id IS NOT NULL THEN 'Organisation'
           WHEN odd.id IS NOT NULL THEN 'Division'
           ELSE 'None'
        END AS source_table
    FROM
        elections_election ee
        LEFT JOIN organisations_divisiongeographysubdivided odd
               ON ee.division_geography_id = odd.division_geography_id
        LEFT JOIN organisations_organisationgeographysubdivided ogd
               ON ee.organisation_geography_id = ogd.organisation_geography_id
    WHERE
        current_status = 'Approved'
        AND ("poll_open_date" >= '{date}' OR "current")
        AND NOT (NOT "current" AND "current" IS NOT NULL)
        AND group_type IS NULL
    """


class Command(BaseCommand):
    help = "Export a csv of current ballots to s3 along with geoms as wkt. Mostly for doign queries with in Athena"

    def add_arguments(self, parser):
        parser.add_argument(
            "--bucket",
            help="s3 bucket to export to",
            action="store",
            required=True,
        )
        parser.add_argument(
            "--prefix",
            help="s3 prefix (without bucket) to export to",
            action="store",
            required=True,
        )
        parser.add_argument(
            "--filename",
            help="Name of file to export to.",
            action="store",
            default="current_elections.csv",
        )
        parser.add_argument(
            "--from-when",
            help="Export elections from this date. Format: yyyy-mm-dd",
            action="store",
            default=(
                datetime.datetime.now()
                - datetime.timedelta(days=settings.CURRENT_PAST_DAYS)
            )
            .date()
            .strftime("%Y-%m-%d"),
        )

    def handle(self, *args, **options):
        ballots_query = export_sql(options["from_when"])

        with connection.cursor() as cursor:
            self.stdout.write("Executing query to fetch ballots and wkt geoms")
            cursor.execute(ballots_query)
            fieldnames = [column[0] for column in cursor.description]
            rows = cursor.fetchall()

            self.stdout.write("Writing ballots and wkt csv to buffer")
            csv_file = io.StringIO()
            csv_writer = csv.writer(csv_file)

            csv_writer.writerow(fieldnames)
            csv_writer.writerows(rows)
            csv_file.seek(0)
            csv_string = csv_file.getvalue()
            csv_file.close()
            csv_bytes = csv_string.encode("utf-8")

            s3_client = boto3.client("s3")
            bucket = options["bucket"]
            key = f"{options['prefix']}/{options['filename']}"

            self.stdout.write(
                f"Uploading ballots and wkt csv to s3://{bucket}/{key}"
            )
            s3_client.upload_fileobj(io.BytesIO(csv_bytes), bucket, key)

            self.stdout.write("Uploaded CSV to S3")
