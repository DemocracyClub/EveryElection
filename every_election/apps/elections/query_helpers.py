import requests

from django.contrib.gis.geos import Point


class BasePostcodeLookup:
    def __init__(self, postcode):
        self.postcode = postcode.replace(' ', '')

    @property
    def point(self):
        raise NotImplementedError


class MaPitPostcodeLookup(BasePostcodeLookup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fetch_from_mapit()

    def fetch_from_mapit(self):
        if hasattr(self, 'mapit_data'):
            return self.mapit_data

        req = requests.get("https://mapit.mysociety.org/postcode/{}".format(
            self.postcode
        ))
        self.mapit_data = req.json()
        return self.mapit_data

    @property
    def point(self):
        return Point(
            self.mapit_data['wgs84_lon'],
            self.mapit_data['wgs84_lat']
        )
