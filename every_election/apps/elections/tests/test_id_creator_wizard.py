from datetime import date, timedelta

import pytest
from elections.models import ElectedRole, Election, ElectionType
from organisations.models import Organisation
from organisations.tests.factories import (
    OrganisationDivisionFactory,
    OrganisationDivisionSetFactory,
)
from playwright.sync_api import expect


@pytest.fixture()
def id_creator_data():
    today = date.today()
    future = today + timedelta(days=100)
    election_type1 = ElectionType.objects.get(election_type="local")
    org1 = Organisation.objects.create(
        official_identifier="TEST1",
        organisation_type="local-authority",
        official_name="Test Council",
        slug="test",
        territory_code="ENG",
        election_name="Test Council local elections",
        start_date=date(2016, 10, 1),
    )
    ElectedRole.objects.create(
        election_type=election_type1,
        organisation=org1,
        elected_title="Local Councillor",
        elected_role_name="Councillor for Test Council",
    )
    org2 = Organisation.objects.create(
        official_identifier="TEST2",
        organisation_type="local-authority",
        official_name="Test 2 Council",
        slug="test2",
        territory_code="ENG",
        election_name="Test 2 Council local elections",
        start_date=date(2016, 10, 1),
    )
    ElectedRole.objects.create(
        election_type=election_type1,
        organisation=org2,
        elected_title="Local Councillor",
        elected_role_name="Councillor for Test 2 Council",
    )
    div_set = OrganisationDivisionSetFactory(
        organisation=org2, start_date=org2.start_date, end_date=future
    )
    OrganisationDivisionFactory(
        divisionset=div_set,
        name="Test Div 1",
        slug="test-div",
        seats_total=3,
    )
    OrganisationDivisionFactory(
        divisionset=div_set, name="Test Div 2", slug="test-div-2"
    )


def test_date_warning_shown(page, live_server, settings):
    settings.DEBUG = True
    page.goto(f"{live_server.url}/id_creator/date/")
    expect(page).to_have_title("Poll Date | Democracy Club Elections")
    page.locator("#id_date-date_0").fill("1")
    page.locator("#id_date-date_1").fill("")
    page.locator("#id_date-date_2").fill("")
    expect(page.locator("#id_creator_date")).not_to_contain_text(
        "UK elections are almost always on a Thursday"
    )
    page.locator("#id_date-date_1").fill("1")
    expect(page.locator("#id_creator_date")).not_to_contain_text(
        "UK elections are almost always on a Thursday"
    )
    page.locator("#id_date-date_2").fill("2023")
    page.locator("#id_date-date_2").blur()
    expect(page.locator("#id_creator_date")).to_contain_text(
        "UK elections are almost always on a Thursday"
    )
    page.locator("#id_date-date_0").fill("5")
    page.locator("#id_date-date_0").blur()
    expect(page.locator("#id_creator_date")).not_to_contain_text(
        "UK elections are almost always on a Thursday"
    )


def test_full_id_creation(page, live_server, id_creator_data, settings):
    settings.DEBUG = True
    # We shouldn't have any elections
    assert Election.private_objects.count() == 0

    # Open the home page, click to add a new election
    page.goto(live_server.url)
    page.get_by_role("link", name="Add a new election").click()

    # Enter a date
    page.locator("#id_date-date_0").fill("5")
    page.locator("#id_date-date_1").fill("1")
    page.locator("#id_date-date_2").fill("2023")
    page.locator("#id_date-date_2").blur()
    page.get_by_role("button", name="Submit").click()

    # Select the election type
    page.get_by_text("Local elections").click()
    page.get_by_role("button", name="Submit").click()

    # Select the council
    page.get_by_text("Test 2 Council").click()
    page.get_by_role("button", name="Submit").click()

    # Mark all seats as contested
    page.get_by_role("button", name="All Up").click()
    page.get_by_role("button", name="Submit").click()

    # Create the IDs
    page.get_by_role("button", name="Create IDs").click()

    # We should have 4 elections
    assert Election.private_objects.count() == 4
    assert list(
        Election.private_objects.values_list("election_id", flat=True)
    ) == [
        "local.2023-01-05",
        "local.test2.2023-01-05",
        "local.test2.test-div.2023-01-05",
        "local.test2.test-div-2.2023-01-05",
    ]
