import datetime
import hashlib
import sys
from datetime import timedelta
from typing import Optional
from urllib.parse import urljoin

import requests
from dateutil.parser import parse
from django.conf import settings
from elections.models import (
    ElectedRole,
    Election,
    ElectionSubType,
    ElectionType,
    Explanation,
    MetaData,
)
from organisations.models import (
    Organisation,
    OrganisationDivision,
    OrganisationDivisionSet,
)


class ParentDoesNotExist(ValueError):
    ...


class ReplacementDoesNotExist(ValueError):
    ...


class ElectionSyncer:
    def __init__(self, since=None, stdout=None, stderr=None):
        self.since = since
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr
        self.ELECTION_SUBTYPE_CACHE = {}
        self.ELECTED_ROLE_CACHE = {}
        self.ELECTION_TYPE_CACHE = {}

    def add_single_election(self, result: dict):
        try:
            election_model = Election.private_objects.get(
                election_id=result["election_id"]
            )
        except Election.DoesNotExist:
            election_model = Election(election_id=result["election_id"])

        # Always get the org before anything else, as various other keys need it
        # (e.g to get the correct division set)
        if result.get("group_type") != "election":
            election_model.organisation = self.get_organisation(
                result.get("organisation")
            )

        for key, value in result.items():
            if key == "poll_open_date":
                election_model.poll_open_date = parse(value).date()
                continue
            if key == "election_type":
                election_model.election_type = self.get_election_type(
                    result["election_type"]["election_type"]
                )
                continue
            if key == "organisation" and value:
                continue
            if key == "division" and value:
                try:
                    divisionset = OrganisationDivisionSet.objects.get(
                        organisation=election_model.organisation,
                        start_date=value["divisionset"]["start_date"],
                    )
                except OrganisationDivisionSet.DoesNotExist:
                    # In some case we might have changed the start date
                    # for an existing divisionset. This is rare, but one
                    # high profile example is the unknown divisionset start date
                    # of the 2024/2025 general election.
                    # We can manage this by looking for the short_title
                    try:
                        divisionset = OrganisationDivisionSet.objects.filter(
                            organisation=election_model.organisation,
                            short_title=value["divisionset"]["short_title"],
                        ).get()
                    except OrganisationDivisionSet.DoesNotExist:
                        raise
                    # We have a new divisionset with a new start_date, so we
                    # need to set the end date of the old divisionset
                    # before updating this ones start_date
                    previous_divisionset = (
                        OrganisationDivisionSet.objects.filter(
                            organisation=election_model.organisation
                        )
                        .filter_by_date(election_model.poll_open_date)
                        .get()
                    )
                    previous_divisionset.end_date = parse(
                        value["divisionset"]["start_date"]
                    ) - timedelta(days=1)
                    previous_divisionset.save()
                    divisionset.start_date = value["divisionset"]["start_date"]
                    divisionset.save()

                if (
                    not divisionset.end_date
                    and value["divisionset"]["end_date"]
                ) or (
                    divisionset.end_date
                    and divisionset.end_date.isoformat()
                    != value["divisionset"]["end_date"]
                ):
                    # Two Special cases:
                    # 1: Where there is no end date on the DivisionSet and so we set it,
                    # 2: Where there is an end date, but it's changed (likely due to an upcoming boundary change)
                    # in this case, update the DivisionSet's end date
                    election_model.division.divisionset.end_date = value[
                        "divisionset"
                    ]["end_date"]
                    election_model.division.divisionset.save()

                election_model.division = OrganisationDivision.objects.get(
                    official_identifier=value["official_identifier"],
                    divisionset__start_date=value["divisionset"]["start_date"],
                    divisionset__organisation=election_model.organisation,
                )

                continue
            if key == "identifier_type":
                key = "group_type"
                if value == "ballot":
                    value = None
            if key == "voting_system" and value:
                value = value["slug"]
            if key == "elected_role" and value:
                election_model.elected_role = self.get_elected_role(
                    result["elected_role"]
                )
                continue
            if key == "group" and value:
                try:
                    parent = Election.private_objects.get(election_id=value)
                except Election.DoesNotExist:
                    raise ParentDoesNotExist(f"Can't find {value}")
                election_model.group = parent
                continue
            if key in ["replaced_by"]:
                continue
            if key == "replaces" and value:
                if result["group_type"]:
                    # "replaces" is never valid for a group type
                    continue
                try:
                    replaces_election = Election.private_objects.get(
                        election_id=value
                    )
                except Election.DoesNotExist:
                    raise ReplacementDoesNotExist(
                        f"Can't find replacement {value}"
                    )
                election_model.replaces = replaces_election
                continue
            if key == "explanation" and value:
                """
                Because we don't expose the explanation description in the API we're not going to know if one already
                exists exact by looking at the value. If the value doesn't exist, we need to create a new Explanation
                model, so we just make up a name to show that it's been imported. The name is the hash of the value to
                ensure we link imported explanations to unique values.

                """
                try:
                    explanation = Explanation.objects.filter(
                        explanation=value
                    ).first()
                except Explanation.DoesNotExist:
                    explanation_hash = int(
                        hashlib.sha1(value.encode("utf-8")).hexdigest(), 16
                    ) % (10**8)
                    explanation = Explanation.objects.create(
                        explanation=value,
                        description=f"Imported explanation {explanation_hash}",
                    )
                election_model.explanation = explanation
                continue
            if key == "metadata" and value:
                keys = list(value.keys())
                election_model.metadata, _ = MetaData.objects.get_or_create(
                    description=value[keys[0]]["title"], data=value
                )
                continue

            if key == "election_subtype" and value:
                self.get_election_subtype(
                    election_model.election_type, value["election_subtype"]
                )
                continue

            setattr(election_model, key, value)

        election_model.modified = result["modified"]
        election_model.save(update_modified=False, status="Approved")

    def get_election_type(self, election_type: str):
        if not self.ELECTION_TYPE_CACHE:
            # Populate the entire cache if it's empty
            qs = ElectionType.objects.all()
            for election_type_model in qs:
                self.ELECTION_TYPE_CACHE[
                    election_type_model.election_type
                ] = election_type_model
        return self.ELECTION_TYPE_CACHE[election_type]

    def get_elected_role(self, elected_role: str):
        if not self.ELECTED_ROLE_CACHE:
            # Populate the entire cache if it's empty
            qs = ElectedRole.objects.all()
            for elected_role_model in qs:
                self.ELECTED_ROLE_CACHE[
                    elected_role_model.elected_title
                ] = elected_role_model
        return self.ELECTED_ROLE_CACHE[elected_role]

    def get_organisation(self, organisation_dict: dict):
        organisation = Organisation.objects.get(
            official_identifier=organisation_dict["official_identifier"],
            start_date=organisation_dict["start_date"],
        )
        if organisation.end_date != organisation_dict["end_date"]:
            # update the end date when we see that it's changed
            organisation.end_date = organisation_dict["end_date"]
            organisation.save()
        return organisation

    def get_election_subtype(self, election_type: str, election_subtype: str):
        if not self.ELECTION_SUBTYPE_CACHE:
            # Populate the entire cache if it's empty
            qs = ElectionSubType.objects.all()
            for election_subtype_model in qs:
                if (
                    election_subtype_model.election_type
                    not in self.ELECTION_SUBTYPE_CACHE
                ):
                    self.ELECTION_SUBTYPE_CACHE[
                        election_subtype_model.election_type
                    ] = {}
                self.ELECTION_SUBTYPE_CACHE[
                    election_subtype_model.election_type
                ][
                    election_subtype_model.election_subtype
                ] = election_subtype_model
        return self.ELECTION_SUBTYPE_CACHE[election_type][election_subtype]

    def process_result(self, result: dict):
        try:
            self.add_single_election(result)
        except OrganisationDivision.DoesNotExist:
            self.stderr.write(
                f"Can't add {result['election_id']} because the Division doesn't exits."
            )
        except Organisation.DoesNotExist:
            self.stderr.write(
                f"Can't add {result['election_id']} because the Organisation doesn't exits."
            )
            raise
        except ParentDoesNotExist as e:
            self.stderr.write(
                f"Missing parent ({e}), importing directly before continuing"
            )
            url = urljoin(self.url, result["group"])
            parent_req = requests.get(url)
            self.process_result(parent_req.json())
            self.process_result(result)
        except ReplacementDoesNotExist as e:
            self.stderr.write(
                f"Missing replacement election for ({e}), importing directly before continuing"
            )
            replacement_req = requests.get(
                urljoin(self.url, result["replaces"])
            )
            self.process_result(replacement_req.json())
            self.process_result(result)

    def get_last_modified(
        self, since: Optional[datetime.datetime] = None
    ) -> datetime.datetime:
        if since:
            return since
        try:
            last_modified = (
                Election.private_objects.latest().modified
                - timedelta(hours=1, minutes=1)
            )
        except Election.DoesNotExist:
            last_modified = datetime.datetime(1832, 6, 7)

        return last_modified.replace(tzinfo=None)

    def run_import(self):
        self.url = settings.UPSTREAM_SYNC_URL
        last_modified = self.get_last_modified(self.since)
        self.url = f"{self.url}?modified={last_modified}"
        self.stdout.write(self.url)
        while self.url:
            self.stdout.write(f"Starting import for {last_modified}")
            req = requests.get(self.url)
            req.raise_for_status()
            resp_json = req.json()
            unordered_results = resp_json["results"]
            results = sorted(
                unordered_results, key=lambda d: d["election_id"].count(".")
            )
            for result in results:
                self.process_result(result)
            self.url = resp_json.get("next", None)
