from csv import DictReader
from datetime import datetime

from pytest import mark

from uk_election_timetables.date import days_before
from uk_election_timetables.elections import (
    GreaterLondonAssemblyElection,
    MayoralElection,
    NorthernIrelandAssemblyElection,
    PoliceAndCrimeCommissionerElection,
    ScottishParliamentElection,
    SeneddCymruElection,
    UKParliamentElection,
)

with open("./tests/historic_sopn_data.csv") as f:
    historic_data = list(
        DictReader(row for row in f if not row.startswith("--"))
    )


def read_date(date_as_string):
    return datetime.strptime(date_as_string, "%Y-%m-%d").date()


def same_or_next_day(actual_date, expected_date):
    return days_before(actual_date, 1) <= expected_date <= actual_date


def no_later_than(actual_date, expected_date):
    # We use "up to 3 days before" as a test heuristic, it's good enough
    return days_before(expected_date, 3) <= actual_date <= expected_date


def within_one_day(actual_date, expected_date):
    return same_or_next_day(
        actual_date, expected_date
    ) or actual_date == days_before(expected_date, 1)


def generate_test_id(val):
    return "%s-%s-%s" % (val["election_id"], val["geo_id"], val["sopn_id"])


def generate_test_cases(search, exceptions=None):
    exceptions = exceptions if exceptions is not None else []

    return [
        row
        for row in historic_data
        if search in row["election_id"] and row["election_id"] not in exceptions
    ]


@mark.parametrize("row", generate_test_cases("nia"), ids=generate_test_id)
def test_northern_ireland_assembly(row):
    poll_date = read_date(row["election_date"])

    expected_date = NorthernIrelandAssemblyElection(poll_date).sopn_publish_date

    actual_date = read_date(row["sopn_publish_date"])

    assert same_or_next_day(actual_date, expected_date)


@mark.parametrize("row", generate_test_cases("sp"), ids=generate_test_id)
def test_scottish_parliament(row):
    poll_date = read_date(row["election_date"])

    expected_date = ScottishParliamentElection(poll_date).sopn_publish_date

    actual_date = read_date(row["sopn_publish_date"])

    assert same_or_next_day(actual_date, expected_date)


@mark.parametrize("row", generate_test_cases("naw"), ids=generate_test_id)
def test_old_national_assembly_for_wales(row):
    poll_date = read_date(row["election_date"])

    expected_date = SeneddCymruElection(poll_date).sopn_publish_date

    actual_date = read_date(row["sopn_publish_date"])

    assert same_or_next_day(actual_date, expected_date)


@mark.parametrize("row", generate_test_cases("gla."), ids=generate_test_id)
def test_greater_london_assembly(row):
    poll_date = read_date(row["election_date"])

    expected_date = GreaterLondonAssemblyElection(poll_date).sopn_publish_date

    actual_date = read_date(row["sopn_publish_date"])

    assert no_later_than(actual_date, expected_date)


@mark.parametrize("row", generate_test_cases("pcc"), ids=generate_test_id)
def test_police_and_crime_commissioner(row):
    poll_date = read_date(row["election_date"])

    expected_date = PoliceAndCrimeCommissionerElection(
        poll_date
    ).sopn_publish_date

    actual_date = read_date(row["sopn_publish_date"])

    assert no_later_than(actual_date, expected_date)


@mark.parametrize(
    "row",
    generate_test_cases("mayor", exceptions=["mayor.london.2016-05-05"]),
    ids=generate_test_id,
)
def test_mayoral(row):
    poll_date = read_date(row["election_date"])

    expected_date = MayoralElection(poll_date).sopn_publish_date

    actual_date = read_date(row["sopn_publish_date"])

    assert within_one_day(actual_date, expected_date)


@mark.parametrize(
    "row", generate_test_cases("mayor.london"), ids=generate_test_id
)
def test_mayor_of_london(row):
    poll_date = read_date(row["election_date"])

    expected_date = GreaterLondonAssemblyElection(poll_date).sopn_publish_date

    actual_date = read_date(row["sopn_publish_date"])

    assert within_one_day(actual_date, expected_date)


@mark.parametrize("row", generate_test_cases("parl"), ids=generate_test_id)
def test_uk_parliament(row):
    poll_date = read_date(row["election_date"])

    expected_date = UKParliamentElection(poll_date).sopn_publish_date

    actual_date = read_date(row["sopn_publish_date"])

    assert within_one_day(actual_date, expected_date)
