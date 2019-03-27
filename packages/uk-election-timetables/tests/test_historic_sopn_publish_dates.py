from sopn_publish_date import StatementPublishDate
from datetime import timedelta, datetime
from csv import DictReader
from pytest import mark

sopn_publish_date = StatementPublishDate()

with open("./tests/historic_sopn_data.csv") as f:
    historic_data = list(DictReader(row for row in f if not row.startswith('--')))


def read_date(date_as_string):
    return datetime.strptime(date_as_string, "%Y-%m-%d")


def same_or_next_day(actual_date, expected_date):
    return actual_date == expected_date or actual_date == (
        expected_date + timedelta(days=1)
    )


def within_one_day(actual_date, expected_date):
    return same_or_next_day(actual_date, expected_date) or actual_date == (
        expected_date - timedelta(days=1)
    )


def generate_test_id(val):
    return "%s-%s-%s" % (val["election_id"], val["geo_id"], val["sopn_id"])


def generate_test_cases(type):
    return [row for row in historic_data if type in row["election_id"]]


@mark.parametrize("row", generate_test_cases("nia"), ids=generate_test_id)
def test_northern_irish_assembly(row):

    expected_date = sopn_publish_date.northern_irish_assembly(
        read_date(row["election_date"])
    )

    actual_date = read_date(row["sopn_publish_date"])

    assert same_or_next_day(actual_date, expected_date)


@mark.parametrize("row", generate_test_cases("sp"), ids=generate_test_id)
def test_scottish_parliament(row):
    expected_date = sopn_publish_date.scottish_parliament(
        read_date(row["election_date"])
    )

    actual_date = read_date(row["sopn_publish_date"])

    assert same_or_next_day(actual_date, expected_date)


@mark.parametrize("row", generate_test_cases("naw"), ids=generate_test_id)
def test_national_assembly_for_wales(row):
    expected_date = sopn_publish_date.national_assembly_for_wales(
        read_date(row["election_date"])
    )

    actual_date = read_date(row["sopn_publish_date"])

    assert same_or_next_day(actual_date, expected_date)


@mark.parametrize("row", generate_test_cases("gla."), ids=generate_test_id)
def test_greater_london_assembly(row):
    expected_date = sopn_publish_date.greater_london_assembly(
        read_date(row["election_date"])
    )

    actual_date = read_date(row["sopn_publish_date"])

    assert within_one_day(actual_date, expected_date)


@mark.parametrize("row", generate_test_cases("pcc"), ids=generate_test_id)
def test_police_and_crime_commissioner(row):
    assert within_one_day(
        read_date(row["sopn_publish_date"]),
        sopn_publish_date.for_id(row["election_id"]),
    )


@mark.parametrize("row", generate_test_cases("mayor"), ids=generate_test_id)
def test_mayoral(row):
    assert within_one_day(
        read_date(row["sopn_publish_date"]),
        sopn_publish_date.for_id(row["election_id"]),
    )


