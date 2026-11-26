from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from django.db import IntegrityError, transaction
from elections.tests.factories import ElectedRoleFactory
from elections.utils import ElectionBuilder
from freezegun import freeze_time
from organisations.models import OrganisationDivisionSet
from organisations.tests.factories import (
    DivisionGeographyFactory,
    OrganisationDivisionFactory,
    OrganisationDivisionSetFactory,
)


def test_division_set_by_date(db):
    """
    Test that we can get a division set by a given date
    """

    END_DATE = "2025-05-03"
    FUTURE_DATE = "2025-05-05"

    ds = OrganisationDivisionSetFactory(end_date=END_DATE)

    for i in range(10):
        org_div = OrganisationDivisionFactory(divisionset=ds)

    org = org_div.organisation
    role = ElectedRoleFactory(organisation=org)

    def _make_ids_for_date(date):
        x = ElectionBuilder(role.election_type, date)
        x.with_organisation(org)
        x.with_division(org_div)
        return x

    assert _make_ids_for_date(END_DATE)

    with pytest.raises(ValueError) as excinfo:
        _make_ids_for_date(FUTURE_DATE)
    assert "DivisionSet end date before election date" in str(excinfo.value)


def test_generate_pmtiles_md5_hash(db):
    ds = OrganisationDivisionSetFactory()
    for i in range(10):
        div = OrganisationDivisionFactory(divisionset=ds)
        DivisionGeographyFactory(division=div)

    md5_hash = ds.generate_pmtiles_md5_hash()
    assert len(md5_hash) == 32


@pytest.mark.parametrize(
    "model,field,updated_value",
    [
        ("division", "name", "new name"),
        ("division", "official_identifier", "new id"),
        ("division_geography", "source", "new source"),
        (
            "division_geography",
            "geography",
            "MULTIPOLYGON (((0 0, 0 1, 1 1, 0 0)))",
        ),
    ],
    ids=[
        "division-name",
        "division-official-id",
        "division_geography-source",
        "division_geography-geom",
    ],
)
def test_md5_hash_changes_on_div_or_geog_update(
    db, model, field, updated_value
):
    ds = OrganisationDivisionSetFactory()
    for i in range(10):
        div = OrganisationDivisionFactory(divisionset=ds)
        DivisionGeographyFactory(division=div)
    original_hash = ds.generate_pmtiles_md5_hash()

    if model == "division":
        obj = ds.divisions.first()
    else:
        obj = ds.get_division_geographies().first()
    getattr(obj, field)  # check field exists
    setattr(obj, field, updated_value)
    obj.save()

    new_hash = ds.generate_pmtiles_md5_hash()
    assert original_hash != new_hash


def test_generate_pmtiles_hash_if_absent_on_save(db):
    ds = OrganisationDivisionSetFactory()
    assert ds.pmtiles_md5_hash == ""
    for i in range(10):
        div = OrganisationDivisionFactory(divisionset=ds)
        DivisionGeographyFactory(division=div)

    ds.save()  # should generate hash

    assert ds.pmtiles_md5_hash != ""
    assert len(ds.pmtiles_md5_hash) == 32


def test_pmtiles_hash_not_regenerated_if_already_exists(db):
    with patch(
        "organisations.models.OrganisationDivisionSet.generate_pmtiles_md5_hash",
        return_value="mock_hash",
    ) as mock_generate_hash:
        ds = OrganisationDivisionSetFactory()
        assert ds.pmtiles_md5_hash == ""

        for i in range(10):
            div = OrganisationDivisionFactory(divisionset=ds)
            DivisionGeographyFactory(division=div)

        ds.save()  # should generate hash

        assert ds.pmtiles_md5_hash != ""

        ds.save()  # should not not generate hash
        assert mock_generate_hash.call_count == 1


class TestDivisionSetOverlapConstraint:
    """
    A divisionset's end_date is the last day it is in force (see
    DivisionManager.filter_by_date, which uses end_date__gte), so two
    divisionsets for the same organisation must not share any day.
    """

    @pytest.fixture
    def first_divset(self, db):
        return OrganisationDivisionSetFactory(
            start_date="2017-05-04", end_date="2022-05-04"
        )

    def test_adjacent_divsets_allowed(self, first_divset):
        OrganisationDivisionSetFactory(
            organisation=first_divset.organisation,
            start_date="2022-05-05",
            end_date=None,
        )

    def test_overlapping_divsets_rejected(self, first_divset):
        with pytest.raises(IntegrityError), transaction.atomic():
            OrganisationDivisionSetFactory(
                organisation=first_divset.organisation,
                start_date="2020-01-01",  # in the middle of the range for first_divset
                end_date=None,
            )

    def test_divsets_sharing_boundary_day_rejected(self, first_divset):
        with pytest.raises(IntegrityError), transaction.atomic():
            OrganisationDivisionSetFactory(
                organisation=first_divset.organisation,
                start_date="2022-05-04",  # same as first_divset.enddate
                end_date=None,
            )

    def test_same_dates_for_different_organisations_allowed(self, first_divset):
        OrganisationDivisionSetFactory(
            start_date="2017-05-04", end_date="2022-05-04"
        )


class TestWithLastModified:
    """
    The division set in these tests is saved on 2026-01-01.
    """

    @pytest.fixture
    def divset(self, db):
        with freeze_time("2026-01-01"):
            return OrganisationDivisionSetFactory()

    def get_last_modified(self, divset):
        return (
            OrganisationDivisionSet.objects.with_last_modified()
            .get(pk=divset.pk)
            .last_modified
        )

    def test_without_divisions(self, divset):
        assert self.get_last_modified(divset) == datetime(
            2026, 1, 1, tzinfo=UTC
        )

    def test_division_saved_after_division_set(self, divset):
        with freeze_time("2026-02-01"):
            OrganisationDivisionFactory(divisionset=divset)
        assert self.get_last_modified(divset) == datetime(
            2026, 2, 1, tzinfo=UTC
        )

    def test_division_set_saved_after_divisions(self, divset):
        with freeze_time("2026-02-01"):
            OrganisationDivisionFactory(divisionset=divset)
        with freeze_time("2026-03-01"):
            divset.save()
        assert self.get_last_modified(divset) == datetime(
            2026, 3, 1, tzinfo=UTC
        )

    def test_most_recently_saved_division(self, divset):
        with freeze_time("2026-03-01"):
            OrganisationDivisionFactory(divisionset=divset)
        with freeze_time("2026-02-01"):
            OrganisationDivisionFactory(divisionset=divset)
        assert self.get_last_modified(divset) == datetime(
            2026, 3, 1, tzinfo=UTC
        )

    def test_ignores_other_division_sets_divisions(self, divset):
        with freeze_time("2026-02-01"):
            OrganisationDivisionFactory()
        assert self.get_last_modified(divset) == datetime(
            2026, 1, 1, tzinfo=UTC
        )

    def test_one_row_per_division_set(self, divset):
        OrganisationDivisionFactory(divisionset=divset)
        OrganisationDivisionFactory(divisionset=divset)
        assert OrganisationDivisionSet.objects.with_last_modified().count() == 1

    def test_last_modified_after(self, divset):
        with freeze_time("2026-02-01"):
            OrganisationDivisionFactory(divisionset=divset)
        qs = OrganisationDivisionSet.objects
        assert list(
            qs.last_modified_after(datetime(2026, 1, 15, tzinfo=UTC))
        ) == [divset]
        assert not qs.last_modified_after(
            datetime(2026, 2, 1, tzinfo=UTC)
        ).exists()
