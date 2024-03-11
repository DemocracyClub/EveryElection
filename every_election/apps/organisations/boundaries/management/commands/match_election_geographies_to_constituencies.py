import csv
from collections import deque
from typing import Iterator

from django.contrib.gis.db.models.functions import Area, Intersection, Transform
from django.core.management import BaseCommand
from django.db.models import F, Value
from django.db.models.functions import Coalesce
from elections.models import Election
from organisations.models import Organisation, OrganisationDivision


def get_max_overlap_div(ballot: Election, overlapping_div_ids: Iterator[int]):
    return (
        OrganisationDivision.objects.filter(pk__in=overlapping_div_ids)
        .annotate(
            area=Area(
                Intersection(
                    Transform(F("geography__geography"), 27700),
                    Transform(Value(ballot.geom), 27700),
                )
            )
        )
        .order_by("-area")[0]
    )


class Command(BaseCommand):
    help = (
        "Get largest overlap between election geographies and parl constituencies. "
        "This is useful for figuring out which local party groups will be running local elections."
        "example: python manage.py match_election_geographies_to_constituencies local.2024-05-02"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "election_group",
            action="store",
            help="election group to compare",
        )
        parser.add_argument(
            "--outfile",
            action="store",
            default="election_ids_to_constituencies.csv",
            help="election group to ",
        )

    def handle(self, *args, **options):
        try:
            parent_election = Election.public_objects.get(
                election_id=options["election_group"]
            )
        except Election.DoesNotExist:
            self.stdout.write(
                f"Election object with election_id={options['election_group']} does not exist"
            )
            return

        ballots_with_geoms = self.get_ballots_with_geoms(parent_election)
        parl_spatial_index = self.get_parl_sidx()
        election_ids_to_constituencies = (
            self.get_election_ids_to_constituencies(
                ballots_with_geoms, parl_spatial_index
            )
        )

        outfile = options["outfile"]
        self.write_to_csv(outfile, election_ids_to_constituencies)
        self.stdout.write("...all done.")

    def write_to_csv(self, outfile, data):
        self.stdout.write(f"Writing to {outfile}...")
        with open(outfile, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=data[0].keys())
            writer.writeheader()
            for row in data:
                writer.writerow(row)

    def get_ballots_with_geoms(
        self, parent_election: Election
    ) -> list[Election]:
        self.stdout.write(
            f"Getting all child ballots for {parent_election.election_id}..."
        )
        ballots = []
        queue = deque([parent_election])
        while queue:
            current_election = queue.popleft()
            if current_election.group_type is None:
                ballots.append(current_election)
                continue
            child_elections = list(
                current_election.get_children(Election.public_objects).annotate(
                    geom=Coalesce(
                        F("division_geography__geography"),
                        F("organisation_geography__geography"),
                    )
                )
            )
            queue.extend(child_elections)
        return ballots

    def get_parl_sidx(self):
        try:
            import rtree

            idx = rtree.index.Index()
            parl_org = Organisation.objects.get(official_identifier="parl-hoc")
            parl_divs = parl_org.divisionset.latest().divisions.select_related(
                "geography"
            )
            self.stdout.write(
                f"Building rtree for divs in {parl_org.divisionset.latest()}..."
            )
            for div in parl_divs:
                idx.insert(div.id, div.geography.geography.extent)
            return idx
        except ImportError:
            self.stdout.write(
                "Please install rtree: https://rtree.readthedocs.io/en/latest/install.html"
            )

    def get_election_ids_to_constituencies(
        self, ballots_with_geoms, parl_spatial_index
    ):
        election_ids_to_constituencies = []

        self.stdout.write(
            "Getting parlimentary constiuency with greatest overlap to each ballot..."
        )
        progress_interval = len(ballots_with_geoms) // 29

        for i in range(len(ballots_with_geoms)):
            ballot = ballots_with_geoms[i]
            row = self.ballot_overlap_calc(ballot, parl_spatial_index)

            election_ids_to_constituencies.append(row)

            if progress_interval > 1 and i % progress_interval == 0:
                if (i / progress_interval) % 3 == 0:
                    self.stdout.write(
                        f"{int(10 * i / progress_interval / 3)}", ending=""
                    )
                else:
                    self.stdout.write(".", ending="")
                self.stdout.flush()

        if progress_interval > 1:
            self.stdout.write("100")
        return election_ids_to_constituencies

    def ballot_overlap_calc(self, ballot, parl_spatial_index):
        overlapping_div_ids = parl_spatial_index.intersection(
            ballot.geom.extent
        )
        max_overlap_div = get_max_overlap_div(ballot, overlapping_div_ids)
        overlap_area = int(max_overlap_div.area.sq_m / 1000)
        ballot_area = int(ballot.geom.transform(27700, clone=True).area / 1000)
        if overlap_area > ballot_area:
            # This is because transformations, floats, something something
            overlap_area = ballot_area

        return {
            "election_id": ballot.election_id,
            "constituency_name": max_overlap_div.name,
            "overlap_area": overlap_area,
            "ballot_area": ballot_area,
            "percent_overlap": int((overlap_area / ballot_area) * 100.0),
        }
