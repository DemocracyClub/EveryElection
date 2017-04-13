import requests

from django.contrib.gis.geos import Point


class PostcodeError(Exception):
    pass


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


class ONSPDStaticJsonLookup(BasePostcodeLookup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fetch()
        except:
            raise PostcodeError()

    def fetch(self):
        if hasattr(self, 'data'):
            return self.data
        url_fmt = "https://s3-eu-west-1.amazonaws.com/onspd-static-json/{}"
        req = requests.get(url_fmt.format(self.postcode))
        if req.status_code != 200:
            raise PostcodeError
        self.data = req.json()
        return self.data

    @property
    def point(self):
        return Point(
            self.data['wgs84_lon'],
            self.data['wgs84_lat']
        )

def get_point_from_postcode(postcode):
    methods = [
        ONSPDStaticJsonLookup,
        MaPitPostcodeLookup,
    ]
    for method in methods:
        try:
            return method(postcode).point
        except PostcodeError:
            continue
    raise PostcodeError
