from unittest.mock import patch

import pytest
from elections.tests.factories import ElectedRoleFactory
from elections.utils import ElectionBuilder
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
