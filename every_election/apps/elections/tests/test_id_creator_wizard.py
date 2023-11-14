from datetime import date, timedelta

import pytest
from elections.models import (
    ElectedRole,
    Election,
    ElectionType,
)
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
        organisation=org1, start_date=org1.start_date, end_date=future
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
    div_set2 = OrganisationDivisionSetFactory(
        organisation=org2, start_date=org2.start_date, end_date=future
    )
    OrganisationDivisionFactory(
        divisionset=div_set2,
        name="Test Div 1",
        slug="test-div",
        seats_total=3,
    )
    OrganisationDivisionFactory(
        divisionset=div_set2, name="Test Div 2", slug="test-div-2"
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


def test_subtype_creation(page, live_server, id_creator_data, settings):
    naw_org = Organisation.objects.create(
        official_identifier="naw",
        organisation_type="naw",
        official_name="naw",
        slug="naw",
        territory_code="WLS",
        election_name="National Assembly for Wales elections",
        start_date=date(2016, 10, 1),
    )
    naw_election_type = ElectionType.objects.get(election_type="naw")
    ElectedRole.objects.create(
        election_type=naw_election_type,
        organisation=naw_org,
        elected_title="Assembly Member",
        elected_role_name="Assembly Member for Foo",
    )
    naw_div_set = OrganisationDivisionSetFactory(organisation=naw_org)
    OrganisationDivisionFactory(
        divisionset=naw_div_set,
        name="Test Div 3",
        slug="test-div-3",
        division_election_sub_type="c",
        division_subtype="Constituencies",
    )
    OrganisationDivisionFactory(
        divisionset=naw_div_set,
        name="Test Div 4",
        slug="test-div-4",
        division_election_sub_type="c",
        division_subtype="Constituencies",
    )
    OrganisationDivisionFactory(
        divisionset=naw_div_set,
        name="Test Div 5",
        slug="test-div-5",
        division_election_sub_type="r",
        division_subtype="Regions",
        seats_total=7,
    )
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
    page.get_by_text("National Assembly for Wales elections").click()
    page.get_by_role("button", name="Submit").click()

    # Select the subtype
    page.get_by_text(
        "Constituencies (National Assembly for Wales elections)"
    ).click()
    page.get_by_text("Regions (National Assembly for Wales elections)").click()
    page.get_by_role("button", name="Submit").click()

    # Ensure that all the headings exist
    page.get_by_role("heading", name="Constituencies").click()
    page.get_by_role("heading", name="Regions").click()

    # Ensure seats contrsted are correct
    expect(
        page.get_by_role("group", name="Test Div 5").locator("small")
    ).to_contain_text("Up to 7 seats total")
    expect(
        page.get_by_role("group", name="Test Div 4").locator("small")
    ).to_contain_text("Up to 1 seats total")
    expect(
        page.get_by_role("group", name="Test Div 3").locator("small")
    ).to_contain_text("Up to 1 seats total")

    # Select all up
    page.get_by_role("button", name="All up").click()
    page.get_by_role("button", name="Submit").click()

    # Assert the IDs are on the review screen
    page.get_by_text("naw.2023-01-05").click()
    page.get_by_text("naw.r.2023-01-05").click()

    # Create IDs
    page.get_by_role("button", name="Create IDs").click()

    # We should have 4 elections
    assert Election.private_objects.count() == 6
    assert list(
        Election.private_objects.values_list("election_id", flat=True)
    ) == [
        "naw.2023-01-05",
        "naw.c.2023-01-05",
        "naw.c.test-div-3.2023-01-05",
        "naw.c.test-div-4.2023-01-05",
        "naw.r.2023-01-05",
        "naw.r.test-div-5.2023-01-05",
    ]


def test_multiple_local_elections(page, live_server, id_creator_data, settings):
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

    # Select both councils
    page.get_by_text("Test Council").click()
    page.get_by_text("Test 2 Council").click()
    page.get_by_role("button", name="Submit").click()

    # Ensure that all the headings exist
    page.get_by_role("heading", name="Test Council").click()
    page.get_by_role("heading", name="Test 2 Council").click()

    # Select elections
    page.get_by_text("Scheduled").nth(1).click()
    page.get_by_text("Scheduled").nth(2).click()
    page.get_by_text("By-election").nth(2).click()
    page.get_by_text("Scheduled").nth(4).click()
    page.get_by_role("button", name="Submit").click()

    # Create IDs
    page.get_by_role("button", name="Create IDs").click()

    # We should have 4 elections
    assert Election.private_objects.count() == 7
    assert list(
        Election.private_objects.values_list("election_id", flat=True)
    ) == [
        "local.2023-01-05",
        "local.test.2023-01-05",
        "local.test2.2023-01-05",
        "local.test2.test-div.2023-01-05",
        "local.test2.test-div-2.2023-01-05",
        "local.test.test-div-2.2023-01-05",
        "local.test.test-div.by.2023-01-05",
    ]
