from django.core.management.base import BaseCommand
from django.db import connection
from organisations.models import (
    DivisionGeographySubdivided,
    OrganisationGeographySubdivided,
)


class Command(BaseCommand):
    help = "Populate the subdivided tables"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            self.stdout.write("Orgs")
            cursor.execute(OrganisationGeographySubdivided.POPULATE_SQL)
            self.stdout.write("Divs")
            cursor.execute(DivisionGeographySubdivided.POPULATE_SQL)
            self.stdout.write("Divs")
            cursor.execute(DivisionGeographySubdivided.POPULATE_SQL)
