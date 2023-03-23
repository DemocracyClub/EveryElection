from django.db import connection
from django.core.management.base import BaseCommand
from organisations.models import (
    OrganisationGeographySubdivided,
    DivisionGeographySubdivided,
)


class Command(BaseCommand):
    help = "Populate the subdivided tables"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            self.stdout.write("Orgs")
            cursor.execute(OrganisationGeographySubdivided.POPULATE_SQL)
            self.stdout.write("Divs")
            cursor.execute(DivisionGeographySubdivided.POPULATE_SQL)
