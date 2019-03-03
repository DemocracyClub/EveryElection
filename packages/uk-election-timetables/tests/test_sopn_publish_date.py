from sopn_publish_date import StatementPublishDate
from datetime import datetime
from pytest import fail

sopn_publish_date = StatementPublishDate()


def test_publish_date_local_group():
    try:
        sopn_publish_date.for_id('local.2019-02-21')
        fail("Should have thrown exception")
    except Exception as e:
        assert_exception_has_id(e, 'local.2019-02-21')


def test_publish_date_parliamentary_group():
    try:
        sopn_publish_date.for_id('parl.2017-06-08')
        fail("Should have thrown exception")
    except Exception as e:
        assert_exception_has_id(e, 'parl.2017-06-08')


def test_publish_date_mayoral_group():
    try:
        sopn_publish_date.for_id('mayor.2016-05-05')
        fail("Should have thrown exception")
    except Exception as e:
        assert_exception_has_id(e, 'mayor.2016-05-05')


# Reference election: sp.c.shetland-islands.2016-05-05
def test_publish_date_scottish_parliament():
    publish_date = sopn_publish_date.for_id('sp.c.shetland-islands.2016-05-05')

    assert publish_date == datetime(2016, 4, 1)


# Reference election: naw.c.ceredigion.2016-05-05
def test_publish_date_national_assembly_of_wales():
    publish_date = sopn_publish_date.for_id('naw.c.ceredigion.2016-05-05')

    assert publish_date == datetime(2016, 4, 7)


# Reference election: gla.c.barnet-and-camden.2016-05-05
def test_publish_date_greater_london_assembly():
    publish_date = sopn_publish_date.for_id('gla.c.barnet-and-camden.2016-05-05')

    assert publish_date == datetime(2016, 4, 1)


# Reference election: nia.belfast-east.2017-03-02
def test_publish_date_northern_irish_assembly():
    publish_date = sopn_publish_date.for_id('nia.belfast-east.2017-03-02')

    assert publish_date == datetime(2017, 2, 8)


# Reference election: pcc.avon-and-somerset.2016-05-05
def test_publish_date_police_and_crime_commissioner():
    publish_date = sopn_publish_date.for_id('pcc.avon-and-somerset.2016-05-05')

    assert publish_date == datetime(2016, 4, 8)


# Reference election: local.highland.wester-ross-strathpeffer-and-lochalsh.by.2018-12-06
def test_publish_date_scottish_local():
    publish_date = sopn_publish_date.for_country('scotland', datetime(2018, 12, 6))

    assert publish_date == datetime(2018, 11, 2)


# Reference election: local.belfast.balmoral.2019-05-02
def test_publish_date_northern_ireland_local():
    publish_date = sopn_publish_date.for_country('northern-ireland', datetime(2019, 5, 2))

    assert publish_date == datetime(2019, 4, 8)


def assert_exception_has_id(exception, election_id):
    assert str(exception) == 'Cannot derive country from ambiguous election id [%s]' % election_id
