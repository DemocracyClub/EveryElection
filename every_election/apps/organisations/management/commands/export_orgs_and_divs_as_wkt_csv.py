import csv
import datetime
import json
from pathlib import Path
from typing import Optional

from api.serializers import (
    ElectionSubTypeSerializer,
    OrganisationDivisionSerializer,
    OrganisationDivisionSetSerializer,
    OrganisationSerializer,
)
from dateutil.parser import parse
from django.core.management.base import BaseCommand
from django.db.models import Q
from elections.models import (
    ElectedRole,
    ElectionSubType,
    ElectionType,
)
from elections.utils import election_type_has_divisions
from organisations.models import Organisation, OrganisationDivision
from rest_framework.test import APIRequestFactory

BASE_DATA_PATH = Path("/home/symroe/Data/StaticOrgLayer/")
BASE_DATA_PATH.mkdir(parents=True, exist_ok=True)


class Command(BaseCommand):
    help = "Export a csv of current ballots to s3 along with geoms as wkt. Mostly for doign queries with in Athena"

    def add_arguments(self, parser):
        # parser.add_argument(
        #     "--bucket",
        #     help="s3 bucket to export to",
        #     action="store",
        #     required=True,
        # )
        # parser.add_argument(
        #     "--prefix",
        #     help="s3 prefix (without bucket) to export to",
        #     action="store",
        #     required=True,
        # )
        parser.add_argument(
            "--filename",
            help="Name of file to export to.",
            action="store",
            default="current_elections.csv",
        )
        parser.add_argument(
            "--date",
            help="Export data active for date. Format: yyyy-mm-dd",
            action="store",
            default=(datetime.datetime.now()).date().strftime("%Y-%m-%d"),
        )

    def handle(self, *args, **options):
        self.for_date = options["date"]
        self.id_delimiter = "::"

        factory = APIRequestFactory()
        factory.defaults["SERVER_NAME"] = "elections.democracyclub.org.uk"
        self.request = factory.get("/", secure=True)

        election_type_qs = self.get_election_types()

        with Path("/tmp/layers-of-state-current.csv").open("w") as csv_file:
            self.csv_writer = csv.writer(csv_file)
            for election_type in election_type_qs:
                self.process_election_type(election_type)

    def process_election_type(self, election_type):
        # if election_type.election_type != "gla":
        #     return
        elected_roles = election_type.electedrole_set.filter(
            Q(organisation__end_date=None)
            | Q(organisation__end_date__gte=self.for_date)
        )

        if subtypes := election_type.subtype.all():
            for subtype in subtypes:
                for elected_role in elected_roles:
                    self.process_elected_role(elected_role, subtype=subtype)
        else:
            for elected_role in elected_roles:
                self.process_elected_role(elected_role)

    def elected_role_to_json(self, elected_role: ElectedRole) -> dict:
        return {
            "election_type": {
                "name": elected_role.election_type.name,
                "election_type": elected_role.election_type.election_type,
            },
            "elected_title": elected_role.elected_title,
            "elected_role_name": elected_role.elected_role_name,
        }

    def division_to_json(
        self, div, org, elected_role, subtype: Optional[ElectionSubType] = None
    ) -> dict:
        div_election_qs = (
            div.election_set.all()
            .filter(current_status="Approved")
            .order_by("-poll_open_date")
        )
        if div_election_qs.exists():
            last_election_id = div_election_qs.first().election_id
        else:
            last_election_id = None

        div_json_data = OrganisationDivisionSerializer(
            instance=div, context={"request": self.request}
        )
        div_set_json_data = OrganisationDivisionSetSerializer(
            instance=div.divisionset, context={"request": self.request}
        )

        data = {
            "division": div_json_data.data,
            "divisionset": div_set_json_data.data,
            "elected_role": self.elected_role_to_json(elected_role),
            "last_division_election_id": last_election_id,
        }
        if subtype:
            data["subtype"] = ElectionSubTypeSerializer(
                instance=subtype, context={"request": self.request}
            ).data

        data.update(
            self.org_to_json(org),
        )
        return data

    def org_to_json(
        self, org, elected_role: Optional[ElectedRole] = None, is_gla_a=False
    ) -> dict:
        org_json_data = OrganisationSerializer(
            instance=org, context={"request": self.request}
        )
        last_org_election_id = self.get_last_org_election_id(org, elected_role)
        data = {
            "organisation": org_json_data.data,
            "last_org_election_id": last_org_election_id,
        }
        if elected_role:
            data.update(self.elected_role_to_json(elected_role))
        if is_gla_a:
            data["subtype"] = {
                "name": "Additional",
                "election_subtype": "a",
            }
        return data

    def get_last_org_election_id(self, org, elected_role) -> Optional[str]:
        org_elections_qs = (
            org.election_set.all()
            .filter(elected_role=elected_role)
            .filter(current_status="Approved")
            .order_by("-poll_open_date")
            .filter(group_type=None)
        )
        if org_elections_qs.exists():
            return org_elections_qs.first().election_id
        return None

    def get_election_types(self):
        return (
            ElectionType.objects.exclude(organisation=None)
            .filter(organisation__start_date__lte=self.for_date)
            .filter(
                Q(organisation__end_date__gte=self.for_date)
                | Q(organisation__end_date=None)
            )
            .exclude(election_type="europarl")
            .distinct()
        )

    def process_elected_role(self, elected_role: ElectedRole, subtype=None):
        org = elected_role.organisation
        if org.end_date and org.end_date < parse(self.for_date).date():
            return
        is_gla_a = False
        if (
            elected_role.election_type.election_type == "gla"
            and subtype.election_subtype == "a"
        ):
            is_gla_a = True

        if not is_gla_a and election_type_has_divisions(
            elected_role.election_type
        ):
            divisionset = org.divisionset.filter_by_date(self.for_date).first()
            if not divisionset:
                return
            division_qs = divisionset.divisions.all()
            if subtype:
                division_qs = division_qs.filter(
                    division_election_sub_type=subtype.election_subtype
                )
            for division in division_qs:
                division_id = self.create_division_id(
                    division, org, elected_role, subtype=subtype
                )
                self.create_division_json(
                    division_id, division, org, elected_role, subtype=subtype
                )

                for geography in division.geography.subdivided.all():
                    self.csv_writer.writerow(
                        [division_id, geography.geography.wkt]
                    )
            return

        org_id = self.create_org_id(org, elected_role, is_gla_a=is_gla_a)
        # See https://github.com/DemocracyClub/EveryElection/issues/2185
        if org_id in [
            "O::TOB::mayor",  # Role no longer exists, we never ran an election for it
            "O::LIV::mayor",  # Role no longer exists
            "O::BST::mayor",  # Role no longer exists
        ]:
            return
        self.create_org_json(org_id, org, elected_role, is_gla_a=is_gla_a)

        for geography in org.get_geography(self.for_date).subdivided.all():
            self.csv_writer.writerow([org_id, geography.geography.wkt])

    def create_division_id(
        self,
        division,
        org,
        elected_role,
        subtype: Optional[ElectionSubType] = None,
    ):
        parts = [
            "D",  # Indicates this is a division
            org.official_identifier,  # Org ID
            str(division.divisionset.start_date),  # DivisionSet start date
            division.official_identifier,  # Div ID
            elected_role.election_type.election_type,  # Role
        ]
        if subtype:
            parts.append(subtype.election_subtype)

        return self.id_delimiter.join(parts)

    def create_division_json(
        self,
        division_id: str,
        division: OrganisationDivision,
        org: Organisation,
        elected_role: ElectedRole,
        subtype: Optional[ElectionSubType] = None,
    ):
        json_path = BASE_DATA_PATH / f"{division_id}.json"
        with json_path.open("w") as f:
            f.write(
                json.dumps(
                    self.division_to_json(division, org, elected_role, subtype),
                    indent=4,
                )
            )

    def create_org_json(
        self,
        org_id,
        org: Organisation,
        elected_role: ElectedRole,
        is_gla_a=False,
    ):
        json_path = BASE_DATA_PATH / f"{org_id}.json"
        with json_path.open("w") as f:
            f.write(
                json.dumps(
                    self.org_to_json(org, elected_role, is_gla_a=is_gla_a),
                    indent=4,
                )
            )

    def create_org_id(self, org, elected_role, is_gla_a):
        parts = [
            "O",  # Indicates this is an org
            org.official_identifier,  # Org ID
            elected_role.election_type.election_type,
        ]
        if is_gla_a:
            parts.append("a")
        return self.id_delimiter.join(parts)
