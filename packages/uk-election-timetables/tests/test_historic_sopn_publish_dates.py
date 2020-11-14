from uk_election_timetables.sopn import StatementPublishDate
from datetime import timedelta, datetime
from csv import DictReader
from pytest import mark
from warnings import catch_warnings, simplefilter

sopn_publish_date = StatementPublishDate()

with open("./tests/historic_sopn_data.csv") as f:
    historic_data = list(DictReader(row for row in f if not row.startswith("--")))


def read_date(date_as_string):
    return datetime.strptime(date_as_string, "%Y-%m-%d").date()


def same_or_next_day(actual_date, expected_date):
    return actual_date == expected_date or actual_date == (
        expected_date + timedelta(days=1)
    )


def no_later_than(actual_date, expected_date):
    return actual_date == expected_date or actual_date == (
        expected_date - timedelta(days=1)
    )


def within_one_day(actual_date, expected_date):
    return same_or_next_day(actual_date, expected_date) or actual_date == (
        expected_date - timedelta(days=1)
    )


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

    expected_date = sopn_publish_date.northern_ireland_assembly(
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
    with catch_warnings():
        simplefilter("ignore")

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
    expected_date = sopn_publish_date.police_and_crime_commissioner(
        read_date(row["election_date"])
    )

    actual_date = read_date(row["sopn_publish_date"])

    assert no_later_than(actual_date, expected_date)


@mark.parametrize(
    "row",
    generate_test_cases("mayor", exceptions=["mayor.london.2016-05-05"]),
    ids=generate_test_id,
)
def test_mayoral(row):
    expected_date = sopn_publish_date.mayor(read_date(row["election_date"]))

    actual_date = read_date(row["sopn_publish_date"])

    assert within_one_day(actual_date, expected_date)


@mark.parametrize("row", generate_test_cases("mayor.london"), ids=generate_test_id)
def test_mayor_of_london(row):
    expected_date = sopn_publish_date.greater_london_assembly(
        read_date(row["election_date"])
    )

    actual_date = read_date(row["sopn_publish_date"])

    assert within_one_day(actual_date, expected_date)


@mark.parametrize("row", generate_test_cases("parl"), ids=generate_test_id)
def test_uk_parliament(row):
    expected_date = sopn_publish_date.uk_parliament(read_date(row["election_date"]))

    actual_date = read_date(row["sopn_publish_date"])

    assert within_one_day(actual_date, expected_date)
