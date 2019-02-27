from sopn_publish_date import sopn_publish_date_for_id
from datetime import datetime
from pytest import fail


def test_publish_date_english_local():
    try:
        sopn_publish_date_for_id('local.2019-02-21')
        fail("Should have thrown exception")
    except Exception as e:
        assert_exception_has_id(e, 'local.2019-02-21')


def test_publish_date_parliamentary():

    try:
        sopn_publish_date_for_id('parl.2017-06-08')
        fail("Should have thrown exception")
    except Exception as e:
        assert_exception_has_id(e, 'parl.2017-06-08')


# Reference election: sp.c.shetland-islands.2016-05-05
def test_publish_date_scottish_parliament():

    publish_date = sopn_publish_date_for_id('sp.c.shetland-islands.2016-05-05')

    assert publish_date == datetime(2016, 4, 1)


# Reference election: naw.c.ceredigion.2016-05-05
def test_publish_date_national_assembly_of_wales():

    publish_date = sopn_publish_date_for_id('naw.c.ceredigion.2016-05-05')

    assert publish_date == datetime(2016, 4, 7)


# Reference election: gla.c.barnet-and-camden.2016-05-05
def test_publish_date_greater_london_assembly():

    publish_date = sopn_publish_date_for_id('gla.c.barnet-and-camden.2016-05-05')

    assert publish_date == datetime(2016, 4, 1)


def assert_exception_has_id(exception, election_id):
    assert str(exception) == 'Cannot derive country from ambiguous election id [%s]' % election_id
