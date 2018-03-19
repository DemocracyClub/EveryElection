import abc
import requests

from django.contrib.gis.geos import Point


class PostcodeError(Exception):
    pass


class BasePostcodeLookup(metaclass=abc.ABCMeta):
    def __init__(self, postcode):
        self.postcode = postcode.replace(' ', '')

    @property
    @abc.abstractmethod
    def point(self):
        pass


class BaseMaPitPostcodeLookup(BasePostcodeLookup, metaclass=abc.ABCMeta):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fetch_from_mapit()

    @property
    @abc.abstractmethod
    def mapit_base(self):
        pass

    def fetch_from_mapit(self):
        if hasattr(self, 'mapit_data'):
            return self.mapit_data

        req = requests.get("{}/postcode/{}".format(
            self.mapit_base,
            self.postcode
        ))
        if req.status_code != 200:
            raise PostcodeError
        try:
            self.mapit_data = req.json()
        except ValueError:
            raise PostcodeError
        return self.mapit_data

    @property
    def point(self):
        if not 'wgs84_lon' in self.mapit_data:
            raise PostcodeError
        return Point(
            self.mapit_data['wgs84_lon'],
            self.mapit_data['wgs84_lat']
        )


class mySocietyMapitPostcodeLookup(BaseMaPitPostcodeLookup):
    mapit_base = "https://mapit.mysociety.org/"


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
    postcode = postcode.upper()
    methods = [
        ONSPDStaticJsonLookup,
        mySocietyMapitPostcodeLookup,
    ]
    for method in methods:
        try:
            return method(postcode).point
        except PostcodeError:
            continue
    raise PostcodeError
