from datetime import datetime

from django.core.management.base import BaseCommand

from organisations.models import Organisation, OrganisationDivision


class Command(BaseCommand):
    def output_org(self, org):
        self.stdout.write(
            "\t {} {}, {}: {} ({})".format(
                org.territory_code,
                org.official_identifier,
                org.start_date.isoformat(),
                org,
                org.official_identifier,
            )
        )

    def handle(self, **options):
        seen = set()
        self.stdout.write("OrganisationDivisions")
        for org_div in OrganisationDivision.objects.filter(
            divisionset__start_date__gte=datetime.today(), geography=None
        ).order_by("organisation__official_name"):
            if org_div.organisation not in seen:
                self.stdout.write(
                    "\t",
                    "{} {}:{}".format(
                        org_div.organisation.territory_code,
                        org_div.organisation.official_identifier,
                        org_div.organisation,
                    ),
                )
                seen.add(org_div.organisation)

        self.stdout.write("Organisations")
        for org in Organisation.objects.all().order_by("official_name"):

            if org.geographies.count() == 0:
                self.output_org(org)
                continue

            for geog in org.geographies.all():
                if not geog.geography:
                    self.output_org(org)
