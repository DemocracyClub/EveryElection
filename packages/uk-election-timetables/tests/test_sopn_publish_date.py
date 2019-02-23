from sopn_publish_date import sopn_publish_date
from datetime import datetime


# Reference election:
def test_publish_date_english_local():

    publish_date = sopn_publish_date('local.cardiff.2019-02-21')

    assert publish_date == datetime(2019, 1, 25)


# Reference election: parl.islington-north.2017-06-08
def test_publish_date_parliamentary():

    publish_date = sopn_publish_date('parl.islington-north.2017-06-08')

    assert publish_date == datetime(2017, 5, 11)


# Reference election: sp.c.shetland-islands.2016-05-05
def test_publish_date_scottish_parliament():

    publish_date = sopn_publish_date('sp.c.shetland-islands.2016-05-05')

    assert publish_date == datetime(2016, 4, 1)

