from datetime import datetime

from django.contrib.gis.geos import MultiPolygon, Polygon
from django.core.management import BaseCommand
from django.db import transaction
from elections.models import ElectedRole, ElectionType
from organisations.models import Organisation, OrganisationGeography
from slugify import slugify


def union_list(geoms: [MultiPolygon]) -> MultiPolygon:
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
    Creates a new combined authority.
    This means creating an Organisation, OrganisationGeography and an ElectedRole (Mayor)
    Assumes it will be English.
    Example:
    python manage.py create_combined_authority \
      --official-name 'The York and North Yorkshire Combined Authority' \
      --common-name 'The York and North Yorkshire Combined Authority' \
      --identifier YNYC \
      --constituent-councils E06000014 E06000065 \
      --slug york-and-north-yorkshire-ca \
      --legislation https://www.legislation.gov.uk/uksi/2023/1432/contents/made \
      --start-date 2024-05-02     
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--official-name",
            action="store",
            required=True,
            help="Official name of the new combined authority",
        )
        parser.add_argument(
            "--common-name",
            action="store",
            required=True,
            help="Common name of the new combined authority",
        )
        parser.add_argument(
            "--identifier",
            action="store",
            required=True,
            help="Official identifier of the new combined authority",
        )
        parser.add_argument(
            "--constituent-councils",
            action="store",
            nargs="+",
            required=False,
            help="Space seperated list of gss codes of source boundaries ",
        )
        parser.add_argument(
            "--slug",
            action="store",
            required=False,
            help="Slug for the new combined authority",
        )
        parser.add_argument(
            "--legislation",
            action="store",
            required=False,
            help="Legislation URL for the new combined authority",
        )
        parser.add_argument(
            "--start-date",
            action="store",
            required=True,
            help="Start Date of the new CA yyyy-mm-dd",
        )
        parser.add_argument(
            "--exterior-ring",
            action="store_true",
            required=False,
            default=False,
            help="Only return the exterior ring of the combined geographies. "
            "This will remove small 'sliver holes' but isn't what you want if there is meant to be internal rings, "
            "as there is not threshold for size.",
        )

    @transaction.atomic
    def handle(self, *args, **params):
        # Process params
        org_identifier = params["identifier"]
        org_official_name = params["official_name"]
        org_common_name = params["common_name"]
        if params.get("slug", None):
            org_slug = params["slug"]
        else:
            org_slug = slugify(org_common_name)
        org_legislation = params[("legislation")]
        org_start_date = datetime.strptime(params["start_date"], "%Y-%m-%d")

        # Create the Organisation
        ca_organisation = Organisation.objects.create(
            official_identifier=org_identifier,
            official_name=org_official_name,
            common_name=org_common_name,
            slug=org_slug,
            organisation_type="combined-authority",
            territory_code="ENG",
            election_name=org_official_name,
            start_date=org_start_date,
            legislation_url=org_legislation,
        )

        # Create the OrganisationGeography
        if params.get("constituent_councils", None):
            constituent_geoms = OrganisationGeography.objects.filter(
                gss__in=params["constituent_councils"]
            ).values_list("geography", flat=True)

            ca_geom = union_list(constituent_geoms)
            if params.get("exterior_ring", None):
                ca_geom = extract_exterior_ring(ca_geom)
            OrganisationGeography.objects.create(
                start_date=org_start_date,
                legislation_url=org_legislation,
                geography=ca_geom,
                organisation=ca_organisation,
            )

        # Create the ElectedRole
        ElectedRole.objects.create(
            elected_title="Mayor",
            election_type=ElectionType.objects.get(election_type="mayor"),
            organisation=ca_organisation,
            elected_role_name=f"Mayor of {org_official_name}",
        )
