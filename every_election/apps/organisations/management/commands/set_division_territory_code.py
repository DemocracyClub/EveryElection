from django.core.management.base import BaseCommand
from organisations.models import OrganisationDivision

GSS_TO_NATION = {
    "W": "WLS",
    "E": "ENG",
    "N": "NIR",
    "S": "SCT",
}

ORG_TYPE_TO_NATION = {
    "gla": "ENG",
    "nia": "NIR",
    "sp": "SCT",
    "naw": "WLS",
    "senedd": "WLS",
}


class Command(BaseCommand):
    help = "Sets the `territory_code` value for any division that doesn't have one."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry-run",
            help="Don't commit changes",
        )
        super().add_arguments(parser)

    def handle(self, *args, **options):
        divisions = OrganisationDivision.objects.filter(
            territory_code=""
        ).order_by("official_identifier")
        self.stdout.write(
            f"Found {divisions.count()} divisions with missing territory_code"
        )

        messages = {
            "ced": [],
            "org_type": [],
            "gss": [],
            "parent_gss": [],
            "fail": [],
        }

        for div in divisions:
            if div.division_type == "CED":
                div.territory_code = "ENG"
                messages["ced"].append(
                    f"Division {div.official_identifier}: Setting territory_code='ENG'. Reason: CEDs are always in England."
                )

            elif div.organisation.organisation_type in ORG_TYPE_TO_NATION:
                territory_code = ORG_TYPE_TO_NATION[
                    div.organisation.organisation_type
                ]
                div.territory_code = territory_code
                messages["org_type"].append(
                    f"Division {div.official_identifier}: Setting territory_code='{territory_code}'. Reason: Org type '{div.organisation.organisation_type}' implies territory '{territory_code}'"
                )

            elif div.official_identifier.startswith("gss:"):
                gss_code = div.official_identifier[4:]
                gss_head = gss_code[0]
                territory_code = GSS_TO_NATION[gss_head]
                div.territory_code = territory_code
                messages["gss"].append(
                    f"Division {div.official_identifier}: Setting territory_code='{territory_code}'. Reason: GSS code '{gss_code}' starts with '{gss_head}'"
                )

            elif div.organisation.geographies.count() > 0:
                # Note: This shortcut would not be right if an organisation moved
                # from one country to another, but lets ignore that edge case.
                org_geo = div.organisation.geographies.latest()
                gss_head = org_geo.gss[0]
                territory_code = GSS_TO_NATION[gss_head]
                div.territory_code = territory_code
                messages["parent_gss"].append(
                    f"Division {div.official_identifier}: Setting territory_code='{territory_code}'. Reason: Division is a child of {div.organisation.official_name}. Parent GSS code '{org_geo.gss}' starts with '{gss_head}'"
                )
            else:
                messages["fail"].append(
                    f"Division {div.official_identifier}: Not setting a Territory code."
                )

        self.write_logs(messages, divisions)

        if not options["dry-run"]:
            self.stdout.write("Saving records..")
            for div in divisions:
                div.save()
            self.stdout.write("..Done")
        else:
            self.stdout.write("NOT saving anything!")

        divisions = OrganisationDivision.objects.filter(
            territory_code=""
        ).order_by("official_identifier")
        self.stdout.write(
            f"{divisions.count()} divisions still have missing territory_code"
        )

    def write_logs(self, messages, divisions):
        found = len([div for div in divisions if div.territory_code != ""])
        not_found = divisions.count() - found

        self.stdout.write(f"Setting division code for {found} divisions")
        for key, lines in messages.items():
            if key != "fail":
                for line in lines:
                    self.stdout.write(line)
                self.stdout.write("\n")

        if not_found:
            self.stdout.write(
                f"Could not find division code for {not_found} divisions"
            )
        for line in messages["fail"]:
            self.stdout.write(line)
