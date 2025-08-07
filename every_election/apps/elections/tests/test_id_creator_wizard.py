from datetime import date, timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from elections.models import (
    ElectedRole,
    Election,
    ElectionSubType,
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


def test_full_id_creation_not_logged_in(
    page, live_server, id_creator_data, settings
):
    settings.DEBUG = True
    # We shouldn't have any elections
    assert Election.private_objects.count() == 0

    with (
        patch(
            "elections.views.id_creator.send_event"
        ) as creator_send_event_mock,
        patch("elections.models.send_event") as model_send_event_mock,
    ):
        # Open the home page, click to add a new election
        page.goto(live_server.url)
        page.get_by_role("link", name="Suggest a new election").click()

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
        page.get_by_role("button", name="Suggest IDs").click()

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

    # even though we created election objects
    # we shouldn't push an event if the user is logged out
    # because the status is Suggested
    assert creator_send_event_mock.call_count == 0
    assert model_send_event_mock.call_count == 0


def test_full_id_creation_logged_in(
    page, live_server, id_creator_data, settings, browser
):
    settings.DEBUG = True
    # We shouldn't have any elections
    assert Election.private_objects.count() == 0

    # Create test user
    user = get_user_model().objects.create(
        username="fred", is_superuser=True, is_staff=True
    )
    user.set_password("password")
    group = Group.objects.get(name="moderators")
    user.groups.add(group)
    user.save()

    # Log in
    page.goto(f"{live_server.url}/admin/")
    page.locator("#id_username").fill("fred")
    page.locator("#id_password").fill("password")
    page.locator("input[type=submit]").click()
    # Ensure login worked correctly
    assert any(
        cookie["name"] == "sessionid"
        for cookie in browser.contexts[0].cookies()
    )

    with (
        patch(
            "elections.views.id_creator.send_event"
        ) as creator_send_event_mock,
        patch("elections.models.send_event") as model_send_event_mock,
    ):
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

    # we should push an event if the user is a moderator
    # because the status is Approved
    # but we should only push once, even though we created 4 election objects
    assert creator_send_event_mock.call_count == 1
    assert model_send_event_mock.call_count == 0


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
    page.get_by_role("link", name="Suggest a new election").click()

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
    page.get_by_role("button", name="Suggest IDs").click()

    # We should have 6 elections
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


def test_multiple_local_elections(
    playwright_with_admin, live_server, id_creator_data, settings
):
    """
    Logs in as an admin users to make elections. This, in part, tests that
    admin users don't see the 'suggestion' messages that anonymous users do

    """
    page = playwright_with_admin
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

    # Enter a source for the by-election
    page.get_by_text("Source").nth(1).fill("Found on https://example.com")
    page.get_by_role("button", name="Submit").click()

    # Create IDs
    page.get_by_role("button", name="Create IDs").click()

    # We should have 7 elections
    assert Election.private_objects.count() == 7
    assert list(
        Election.private_objects.values_list("election_id", "source")
    ) == [
        ("local.2023-01-05", ""),
        ("local.test.2023-01-05", ""),
        ("local.test2.2023-01-05", ""),
        ("local.test2.test-div.2023-01-05", ""),
        ("local.test2.test-div-2.2023-01-05", ""),
        ("local.test.test-div-2.2023-01-05", ""),
        ("local.test.test-div.by.2023-01-05", "Found on https://example.com"),
    ]


def test_source_validation_error(page, live_server, id_creator_data, settings):
    page.goto(live_server.url)
    page.get_by_role("link", name="Suggest a new election").click()

    # Enter a date
    page.locator("#id_date-date_0").fill("5")
    page.locator("#id_date-date_1").fill("1")
    page.locator("#id_date-date_2").fill("2023")
    page.locator("#id_date-date_2").blur()
    page.get_by_role("button", name="Submit").click()

    page.get_by_text("Local elections").click()
    page.get_by_role("button", name="Submit").click()

    # Select both councils
    page.get_by_text("Test Council").click()
    page.get_by_role("button", name="Submit").click()

    # Ensure that all the headings exist
    page.get_by_role("heading", name="Test Council").click()

    # Select elections
    page.get_by_text("By-election").nth(1).click()
    page.get_by_role("button", name="Submit").click()

    # Don't enter a source, submitting ends up with a form validation error
    page.get_by_role("button", name="Submit").click()

    # Check that the council heading is there
    expect(page.locator("h2").nth(0)).to_contain_text("Test Council")


def test_gla_a_doesnt_show_division_picker(
    page, live_server, id_creator_data, settings
):
    gla_org = Organisation.objects.create(
        official_identifier="gla",
        organisation_type="gla",
        official_name="gla",
        slug="gla",
        territory_code="ENG",
        election_name="Greater London Assembly elections",
        start_date=date(2016, 10, 1),
    )
    gla_election_type = ElectionType.objects.get(election_type="gla")
    ElectionSubType.objects.get(
        election_subtype="a", election_type=gla_election_type
    )
    ElectedRole.objects.create(
        election_type=gla_election_type,
        organisation=gla_org,
        elected_title="Assembly Member",
        elected_role_name="Assembly Member for Foo",
    )
    settings.DEBUG = True
    # We shouldn't have any elections
    assert Election.private_objects.count() == 0

    # Open the home page, click to add a new election
    page.goto(live_server.url)
    page.get_by_role("link", name="Suggest a new election").click()

    # Enter a date
    page.locator("#id_date-date_0").fill("5")
    page.locator("#id_date-date_1").fill("1")
    page.locator("#id_date-date_2").fill("2023")
    page.locator("#id_date-date_2").blur()
    page.get_by_role("button", name="Submit").click()

    # Select the election type
    page.get_by_text("Greater London Assembly elections").click()
    page.get_by_role("button", name="Submit").click()

    # Select the subtype
    page.get_by_text("Additional (Greater London Assembly elections)").click()
    page.get_by_role("button", name="Submit").click()

    # Assert the IDs are on the review screen
    page.get_by_text("gla.2023-01-05").click()
    page.get_by_text("gla.a.2023-01-05").click()

    # Create IDs
    page.get_by_role("button", name="Suggest IDs").click()

    # We should have 2 elections
    assert Election.private_objects.count() == 2
    assert list(
        Election.private_objects.values_list("election_id", flat=True)
    ) == [
        "gla.2023-01-05",
        "gla.a.2023-01-05",
    ]
