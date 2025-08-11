import pytest
from elections.tests.factories import ElectedRoleFactory
from elections.utils import ElectionBuilder
from organisations.tests.factories import (
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
