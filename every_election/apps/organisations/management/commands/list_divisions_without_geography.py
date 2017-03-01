from datetime import datetime

from django.core.management.base import BaseCommand

from organisations.models import (
    Organisation,
    OrganisationDivision,
)


class Command(BaseCommand):


    def handle(self, **options):
        seen = set()
        print("OrganisationDivisions")
        for org_div in OrganisationDivision.objects.filter(
                divisionset__start_date__gte=datetime.today(),
                geography=None).order_by('organisation__official_name'):
            if org_div.organisation not in seen:
                print("\t", "{} {}:{}".format(
                    org_div.organisation.territory_code,
                    org_div.organisation.official_identifier,
                    org_div.organisation,
                ))
                seen.add(org_div.organisation)

        print("Organisations")
        for org in Organisation.objects.filter(geography=None
                ).order_by('official_name'):
            print("\t {} {}:{} ({})".format(
                org.territory_code,
                org.official_identifier,
                org,
                org.official_identifier,
                ))
