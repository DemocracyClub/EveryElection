from datetime import datetime

from django.contrib.gis.geos import MultiPolygon, Polygon
from django.core.management import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify
from elections.models import ElectedRole, ElectionType
from organisations.models import Organisation, OrganisationGeography


def union_list(geoms: list[MultiPolygon]) -> MultiPolygon:
    combined = geoms[0]
    for geom in geoms[1:]:
        combined = combined.union(geom)
    if isinstance(combined, MultiPolygon):
        return combined
    return MultiPolygon(combined)


def extract_exterior_ring(geom: MultiPolygon) -> MultiPolygon:
    return MultiPolygon([Polygon(p.exterior_ring) for p in geom])


class Command(BaseCommand):
    help = """
    Creates a new unitary authority from constituent councils.
    This creates an Organisation, OrganisationGeography and an ElectedRole (Councillor).
    Assumes territory in England.

    Does NOT create divisions or division set. This will need to be added later, or done separately.

    Example for East Surrey:
    python manage.py create_unitary_authority \
      --official-name 'East Surrey Council' \
      --common-name 'East Surrey' \
      --identifier ESY \
      --constituent-councils E07000207 E07000208 E07000210 E07000211 E07000215 \
      --slug east-surrey \
      --start-date 2026-05-07
      
    Example for West Surrey:
    python manage.py create_unitary_authority \
      --official-name 'West Surrey Council' \
      --common-name 'West Surrey' \
      --identifier WSY \
      --constituent-councils E07000209 E07000212 E07000213 E07000214 E07000216 E07000217 \
      --slug west-surrey \
      --start-date 2026-05-07
      
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--official-name",
            action="store",
            required=True,
            help="Official name of the new unitary authority",
        )
        parser.add_argument(
            "--common-name",
            action="store",
            required=True,
            help="Common name of the new unitary authority",
        )
        parser.add_argument(
            "--identifier",
            action="store",
            required=True,
            help="Official identifier of the new unitary authority (3-letter code)",
        )
        parser.add_argument(
            "--constituent-councils",
            action="store",
            nargs="+",
            required=True,
            help="Space-separated list of GSS codes of constituent district/borough councils",
        )
        parser.add_argument(
            "--gss",
            action="store",
            default="",
            help="GSS code for the new organisation geometry",
        )
        parser.add_argument(
            "--slug",
            action="store",
            required=False,
            help="Slug for the new unitary authority (defaults to slugified common name)",
        )
        parser.add_argument(
            "--legislation",
            action="store",
            required=False,
            help="URL to the legislation creating this authority",
        )
        parser.add_argument(
            "--start-date",
            action="store",
            required=True,
            help="Start date of the new UA (yyyy-mm-dd)",
        )
        parser.add_argument(
            "--exterior-ring",
            action="store_true",
            required=False,
            default=False,
            help="Only return the exterior ring of the combined geographies. "
            "This will remove small 'sliver holes' but isn't what you want if there is meant to be internal rings, "
            "as there is no threshold for size.",
        )

    def create_org(self):
        self.ua_organisation = Organisation.objects.create(
            official_identifier=self.org_identifier,
            official_name=self.org_official_name,
            common_name=self.org_common_name,
            slug=self.org_slug,
            organisation_type="local-authority",
            organisation_subtype="UA",
            territory_code="ENG",
            election_name=f"{self.org_common_name} local election",
            start_date=self.org_start_date,
            legislation_url=self.org_legislation,
        )
        self.stdout.write(
            self.style.SUCCESS(f"Created Organisation: {self.ua_organisation}")
        )

    def create_org_geom(self):
        constituent_geoms = list(
            OrganisationGeography.objects.filter(
                gss__in=self.constituent_councils
            ).values_list("geography", flat=True)
        )

        if len(constituent_geoms) != len(self.constituent_councils):
            found_gss = set(
                OrganisationGeography.objects.filter(
                    gss__in=self.constituent_councils
                ).values_list("gss", flat=True)
            )
            missing = set(self.constituent_councils) - found_gss
            raise CommandError(f"Could not find geographies for: {missing}")

        ua_geom = union_list(constituent_geoms)
        if self.exterior_ring:
            ua_geom = extract_exterior_ring(ua_geom)

        org_geography = OrganisationGeography.objects.create(
            start_date=self.org_start_date,
            legislation_url=self.org_legislation,
            geography=ua_geom,
            gss=self.gss,
            organisation=self.ua_organisation,
            source="Derived from constituent council boundaries",
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Created OrganisationGeography: {org_geography}"
            )
        )

    def create_elected_role(self):
        ElectedRole.objects.create(
            elected_title="Councillor",
            election_type=ElectionType.objects.get(election_type="local"),
            organisation=self.ua_organisation,
            elected_role_name=f"Councillor for {self.org_common_name}",
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Created ElectedRole: Councillor for {self.org_common_name}"
            )
        )

    @transaction.atomic
    def handle(self, *args, **params):
        self.org_identifier = params["identifier"]
        self.org_official_name = params["official_name"]
        self.org_common_name = params["common_name"]
        self.constituent_councils = params["constituent_councils"]
        self.org_slug = params.get("slug") or slugify(self.org_common_name)
        self.org_legislation = params.get("legislation")
        self.org_start_date = datetime.strptime(
            params["start_date"], "%Y-%m-%d"
        ).date()
        self.exterior_ring = params.get("exterior_ring", False)
        self.gss = params["gss"]

        # Create the Organisation
        self.create_org()

        # Create the OrganisationGeography by unioning constituent councils
        self.create_org_geom()

        # Create the ElectedRole for councillors
        self.create_elected_role()

        self.stdout.write(
            self.style.SUCCESS(
                f"\nUnitary authority '{self.org_official_name}' created successfully.\n"
                "Note: No divisions were created."
            )
        )
