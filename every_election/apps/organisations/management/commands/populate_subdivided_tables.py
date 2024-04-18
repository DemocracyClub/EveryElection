from django.core.management.base import BaseCommand
from django.db import connection
from organisations.models import (
    DivisionGeographySubdivided,
    OrganisationGeographySubdivided,
)


class Command(BaseCommand):
    help = "Populate the subdivided tables"

    def add_arguments(self, parser):
        parser.add_argument(
            "--where-missing",
            action="store_true",
            help="Don't truncate table, just update where subdivided geography is missing",
        )

    def handle(self, *args, **options):
        if options.get("where_missing", None):
            org_sql = OrganisationGeographySubdivided.POPULATE_WHERE_MISSING_SQL
            div_sql = DivisionGeographySubdivided.POPULATE_WHERE_MISSING_SQL
        else:
            org_sql = OrganisationGeographySubdivided.POPULATE_SQL
            div_sql = DivisionGeographySubdivided.POPULATE_SQL

        with connection.cursor() as cursor:
            self.stdout.write("Orgs")
            cursor.execute(org_sql)
            self.stdout.write("Divs")
            cursor.execute(div_sql)
